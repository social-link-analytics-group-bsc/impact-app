from collections import defaultdict
from data_collector.pubmed import EntrezClient
from datetime import datetime, date
from django_admin_multiple_choice_list_filter.list_filters import MultipleChoiceListFilter
from django.contrib import admin, messages
from django.db import transaction
from django.http import HttpResponse
from sci_impact.article import ArticleMgm
from sci_impact.models import Scientist, Country, Institution, Affiliation, Article, Authorship, CustomField, \
                              Network, NetworkNode, NetworkEdge, ArtifactCitation, Impact, ImpactDetail, \
                              FieldCitations
from sci_impact.tasks import get_citations, mark_articles_of_inb_pis, fill_affiliation_join_date, get_references, \
                             compute_h_index, update_productivy_metrics, identify_self_citation
from similarity.jarowinkler import JaroWinkler
from data_collector.utils import normalize_transform_text

import csv
import logging
import pathlib
import requests
import re

logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'iso_code')
    actions = ['load_countries']
    ordering = ('name',)
    search_fields = ('name',)

    def load_countries(self, request, queryset):
        api_country = 'https://restcountries.eu/rest/v2/all'
        r = requests.get(api_country)
        r.raise_for_status()  # make sure requests raises an error if it fails
        countries = r.json()

        for country in countries:
            country_name = country['name']
            alpha2_code = country['alpha2Code']
            country_iso_code = country['alpha3Code']
            alternative_names = set()
            alternative_names.add(country['nativeName'])
            if country.get('altSpellings'):
                for alternative_name in country['altSpellings']:
                    if len(alternative_name) > 2:
                        alternative_names.add(alternative_name)
                    elif len(alternative_name) == 2 and alternative_name != alpha2_code:
                        alternative_names.add(alternative_name)
            if country.get('translations'):
                translations_considered = ['en','es','br','de','it','fr','pt', 'nl', 'hr']
                for translation, name in country['translations'].items():
                    if translation in translations_considered:
                        alternative_names.add(name)
            list_alt_names = [alt_name for alt_name in alternative_names if alt_name]
            alt_names_str = ', '.join(list_alt_names)
            logger.info(f"Creating country: {country_name}")
            Country.objects.update_or_create(name=country_name, iso_code=country_iso_code,
                                             defaults={'alternative_names': alt_names_str})
    load_countries.short_description = 'Load list of countries'


@admin.register(Scientist)
class ScientistAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'gender', 'is_pi_inb', 'affiliations', 'articles',
                    'articles_with_citations', 'articles_as_first_author', 'articles_as_last_author',
                    'article_citations', 'h_index')
    ordering = ('last_name', 'articles', 'articles_as_first_author', 'articles_as_last_author')
    search_fields = ('first_name', 'last_name',)
    actions = ['compute_h_index','export_as_csv', 'compute_coauthors_network', 'get_articles_pubmed',
               'identify_possible_duplicates', 'mark_as_duplicate', 'remove_duplicates', 'obtain_pi_collaborator',
               'mark_as_not_duplicate', 'udpate_productivity_metrics']
    list_filter = ('is_pi_inb', 'gender',)
    raw_id_fields = ['scientist_ids', 'most_recent_pi_inb_collaborator']  # to increase the load time of the change view
    objs_created = defaultdict(list)
    countries = []
    regex = re.compile('[,;]+')

    def __get_scientist_affiliations(self, obj):
        all_affiliations = obj.affiliation_set.all().order_by('-departure_date')
        if len(all_affiliations) > 0:
            max_year = all_affiliations[0].departure_date.year
            affiliations_max_year = obj.affiliation_set.filter(departure_date__year=max_year)
            affiliations = []
            for affiliation in affiliations_max_year:
                affiliations.append(affiliation.institution.name)
            return ', '.join(affiliations)
        else:
            return '-'

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = ['first_name', 'last_name', 'gender', 'articles', 'affiliations']
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            info_to_write = [obj.first_name, obj.last_name, obj.gender, obj.articles]
            info_to_write.append(self.__get_scientist_affiliations(obj))
            writer.writerow(info_to_write)
        return response
    export_as_csv.short_description = "Export Selected as CSV"

    def affiliations(self, obj):
        return self.__get_scientist_affiliations(obj)
    affiliations.short_description = 'Last affiliations'

    def __display_feedback_msg(self, request):
        if self.objs_created:
            msg = 'The action was completed successfully!\n'
            for model, objs in self.objs_created.items():
                msg += f"- It was created {len(objs)} objects of the type {model}\n"
            self.message_user(request, msg, level=messages.SUCCESS)
        else:
            msg = 'No objects were created'
            self.message_user(request, msg, level=messages.INFO)
        return msg

    def __get_country_iso_code(self, institution_name):
        for country_dict in self.countries:
            for country in country_dict['names']:
                regex_country = re.compile(f", {country}$")
                if regex_country.search(institution_name):
                    return country_dict['iso_code']
        return ''

    def get_articles_pubmed(self, request, queryset):
        ec = EntrezClient()
        am = ArticleMgm()
        for scientist_obj in queryset:
            scientist_name = scientist_obj.first_name + ' ' + scientist_obj.last_name
            logger.info(f"Getting articles of {scientist_name}")
            results = ec.search(f"{scientist_name}[author]")
            papers = ec.fetch_in_batch_from_history(results['Count'], results['WebEnv'], results['QueryKey'])
            for i, paper in enumerate(papers):
                article_obj, created_objs = am.process_paper(i, paper)
                for type_obj, objs in created_objs.items():
                    if isinstance(objs, list):
                        self.objs_created[type_obj].extend(article_obj)
                    else:
                        self.objs_created[type_obj].append(article_obj)
        self.__display_feedback_msg(request)
    get_articles_pubmed.short_description = 'Get articles (source: PubMed)'

    def remove_duplicates(self, request, queryset):
        duplicate_scientists = []
        scientist_to_keep = None
        for scientist_obj in queryset:
            if scientist_obj.is_duplicate:
                duplicate_scientists.append(scientist_obj)
            else:
                scientist_to_keep = scientist_obj
        alternative_names = []
        for duplicate_scientist in duplicate_scientists:
            # 0) save alternative names
            alternative_names.append(duplicate_scientist.first_name + ' ' + duplicate_scientist.last_name)
            # 1) update scientist metrics
            scientist_to_keep.articles += duplicate_scientist.articles
            scientist_to_keep.articles_as_first_author += duplicate_scientist.articles_as_first_author
            scientist_to_keep.articles_as_last_author += duplicate_scientist.articles_as_last_author
            scientist_to_keep.articles_with_citations += duplicate_scientist.articles_with_citations
            scientist_to_keep.article_citations += duplicate_scientist.article_citations
            scientist_to_keep.books += duplicate_scientist.books
            scientist_to_keep.patents += duplicate_scientist.patents
            scientist_to_keep.datasets += duplicate_scientist.datasets
            scientist_to_keep.tools += duplicate_scientist.tools
            scientist_to_keep.book_citations += duplicate_scientist.book_citations
            scientist_to_keep.dataset_citations += duplicate_scientist.dataset_citations
            scientist_to_keep.patent_citations += duplicate_scientist.patent_citations
            scientist_to_keep.tool_citations += duplicate_scientist.tool_citations
            scientist_to_keep.total_citations += duplicate_scientist.total_citations
            scientist_to_keep.save()
            # 2) update authorship
            authorships = Authorship.objects.filter(author=duplicate_scientist)
            for authorship in authorships:
                authorship.author = scientist_to_keep
                authorship.save()
            # 3) update affiliation
            affiliations = Affiliation.objects.filter(scientist=duplicate_scientist)
            for affiliation in affiliations:
                affiliation.scientist = scientist_to_keep
                affiliation.save()
            # 4) update pi collaborator
            collabs = Scientist.objects.filter(most_recent_pi_inb_collaborator=duplicate_scientist)
            for collab in collabs:
                collab.most_recent_pi_inb_collaborator = scientist_to_keep
                collab.most_recent_pi_inb_collaborator.save()
            # 5) remove duplicate
            Scientist.objects.get(id=duplicate_scientist.id).delete()
        scientist_to_keep.alternative_names = ', '.join(alternative_names)
        scientist_to_keep.possible_duplicate = False
        scientist_to_keep.save()
        msg = f"Records were successfully merged"
        self.message_user(request, msg, level=messages.SUCCESS)
    remove_duplicates.short_description = 'Merge records'

    def mark_as_duplicate(self, request, queryset):
        for scientist_obj in queryset:
            scientist_obj.is_duplicate = True
            scientist_obj.save()
        msg = f"{len(queryset)} records were marked as duplicates"
        self.message_user(request, msg, level=messages.SUCCESS)
    mark_as_duplicate.short_description = 'Mark as duplicate'

    def __insert_collaboration_edges(self, edges, nodes_dict):
        logger.info('Inserting the edges and their attributes')
        edges_to_insert, attrs_to_insert = [], []
        for edge_tuple, edge_val in edges.items():
            node_a_obj = nodes_dict.get(edge_tuple[0])
            node_b_obj = nodes_dict.get(edge_tuple[1])
            edge = NetworkEdge(node_a=node_a_obj, node_b=node_b_obj, network=node_a_obj.network)
            edges_to_insert.append(edge)
            num_collaborations_attr = CustomField(name='num_collaborations', value=edge_val['num_collaborations'])
            attrs_to_insert.append(num_collaborations_attr)
        inserted_edges = NetworkEdge.objects.bulk_create(edges_to_insert)
        logger.info('Inserted edges')
        inserted_attrs = CustomField.objects.bulk_create(attrs_to_insert)
        logger.info('Inserted edge attributes')
        idx_attr = 0
        logger.info('Generating relationships between edges and attributes')
        edge_attrs_to_insert = []
        for inserted_edge in inserted_edges:
            edge_attr = inserted_attrs[idx_attr]
            edge_attrs_to_insert.append(NetworkEdge.attrs.through(networkedge_id=inserted_edge.id,
                                                                  customfield_id=edge_attr.id))
            idx_attr += 1
        NetworkEdge.attrs.through.objects.bulk_create(edge_attrs_to_insert)
        logger.info('Inserted relationship between edges and attributes')

    def __insert_scientist_nodes(self, nodes, network_obj):
        logger.info('Inserting nodes and their attributes')
        nodes_to_insert = []
        attributes_to_insert = []
        for node_name, node_info in nodes.items():
            node_obj = NetworkNode(name=node_name, network=network_obj)
            nodes_to_insert.append(node_obj)
            for attr_name, attr_info in node_info.items():
                attr_obj = CustomField(name=attr_name, value=attr_info['value'], type=attr_info['type'])
                attributes_to_insert.append(attr_obj)
        inserted_nodes = NetworkNode.objects.bulk_create(nodes_to_insert)
        logger.info('Inserted nodes')
        inserted_attrs = CustomField.objects.bulk_create(attributes_to_insert)
        logger.info('Inserted node attributes')
        num_attributes_per_node = 6
        idx_start_attr, idx_end_attr = 0, num_attributes_per_node
        logger.info('Creating relationship between nodes and attributes')
        node_attrs_to_insert = []
        for inserted_node in inserted_nodes:
            node_attrs = inserted_attrs[idx_start_attr:idx_end_attr]
            for inserted_attr in node_attrs:
                node_attrs_to_insert.append(NetworkNode.attrs.through(networknode_id=inserted_node.id,
                                                                      customfield_id=inserted_attr.id))
            idx_start_attr += num_attributes_per_node
            idx_end_attr += num_attributes_per_node
        NetworkNode.attrs.through.objects.bulk_create(node_attrs_to_insert)
        logger.info('Inserted relationship between nodes and attributes')

    def __create_scientist_node(self, scientist_obj, nodes):
        if str(scientist_obj) not in nodes.keys():
            if scientist_obj.most_recent_pi_inb_collaborator:
                pi_collaborator_full_name = str(scientist_obj.most_recent_pi_inb_collaborator)
            else:
                pi_collaborator_full_name = ''
            scientist_dict = {
                'gender': {'value': scientist_obj.gender, 'type': 'str'},
                'num_articles': {'value': scientist_obj.articles, 'type': 'int'},
                'h_index': {'value': scientist_obj.h_index, 'type': 'int'},
                'total_citations': {'value': scientist_obj.total_citations, 'type': 'int'},
                'is_inb_pi': {'value': scientist_obj.is_pi_inb, 'type': 'bool'},
                'inb_pi_collaborator': {'value': pi_collaborator_full_name, 'type': 'str'}
            }
            nodes[str(scientist_obj)] = scientist_dict
            logger.info(f"Created the scientist node {str(scientist_obj)}")
        return nodes

    def __create_update_edge(self, scientist_a, scientist_b, article_id, edges):
        edge_a = (str(scientist_a), str(scientist_b))
        edge_b = (str(scientist_b), str(scientist_a))
        edge = edges.get(edge_a)
        if edge:
            if article_id not in edge['articles']:
                edge['articles'].append(article_id)
                edge['num_collaborations'] += 1
        else:
            edge = edges.get(edge_b)
            if edge:
                if article_id not in edge['articles']:
                    edge['articles'].append(article_id)
                    edge['num_collaborations'] += 1
            else:
                edges[edge_a] = {
                    'num_collaborations': 1,
                    'articles': [article_id]
                }
                logger.info(f"Created a edge between {str(scientist_a)} and {str(scientist_b)}")
        return edges

    def compute_coauthors_network(self, request, queryset):
        nodes, edges = {}, {}
        network_name = 'CollaborationNetwork'
        logger.info(f"Generating the network {network_name}, it might take some time...")
        net_obj = Network(name=network_name, date=datetime.now())
        if 'is_pi_inb__exact' in request.GET.keys():
            only_inb = True
            network_name += 'INB'
        else:
            only_inb = False
        # 0) Load to memory the data of the authorship table
        logger.info('Loading to memory the data of the authorship table')
        authorships = Authorship.objects.all()
        author_authorships, article_authorships = {}, {}
        for authorship in authorships:
            if not author_authorships.get(authorship.author.id):
                author_authorships[authorship.author.id] = [authorship]
            else:
                author_authorships[authorship.author.id].append(authorship)
            if not article_authorships.get(authorship.artifact.id):
                article_authorships[authorship.artifact.id] = [authorship]
            else:
                article_authorships[authorship.artifact.id].append(authorship)
        # 1) Build network in memory
        for scientist_obj in queryset:
            if not scientist_obj.is_pi_inb:
                continue
            nodes = self.__create_scientist_node(scientist_obj, nodes)
            scientist_authorships = author_authorships.get(scientist_obj.id)
            article_ids = []
            for scientist_authorship in scientist_authorships:
                # iterate over the scientists' articles
                article = scientist_authorship.artifact
                if article.id not in article_ids:
                    article_ids.append(article.id)
                    scientist_article_authorships = article_authorships.get(article.id)
                    author_ids = []
                    for scientist_article_authorship in scientist_article_authorships:
                        # iterate over the article's authors
                        author = scientist_article_authorship.author
                        if author.id not in author_ids:
                            if author.id != scientist_obj.id:
                                author_ids.append(author.id)
                                if only_inb:
                                    if author.is_pi_inb:  # create only nodes and edges of INB PIs
                                        nodes = self.__create_scientist_node(author, nodes)
                                        edges = self.__create_update_edge(scientist_obj, author, article.id, edges)
                                else:
                                    nodes = self.__create_scientist_node(author, nodes)
                                    edges = self.__create_update_edge(scientist_obj, author, article.id, edges)
        # 2) Save record into the DB
        with transaction.atomic():
            net_obj.save()
            self.__insert_scientist_nodes(nodes, net_obj)
            nodes_db = NetworkNode.objects.filter(network=net_obj)
            nodes_dict = {}
            for node_db in nodes_db:
                nodes_dict[node_db.name] = node_db
            self.__insert_collaboration_edges(edges, nodes_dict)
        msg = f"The collaboration network was computed successfully"
        self.message_user(request, msg, level=messages.SUCCESS)
    compute_coauthors_network.short_description = 'Generate collaboration network'

    def obtain_pi_collaborator(self, request, queryset):
        for scientist_obj in queryset:
            logger.info(f"Obtaining the pi collaborator of {scientist_obj.first_name + ' ' + scientist_obj.last_name}")
            if scientist_obj.most_recent_pi_inb_collaborator:
                continue
            if scientist_obj.is_pi_inb:
                scientist_obj.most_recent_pi_inb_collaborator = scientist_obj
                scientist_obj.save()
                continue
            else:
                inb_pi_collaborations = {}
                scientist_authorships = Authorship.objects.filter(author_id=scientist_obj.id)
                article_ids = []
                for scientist_authorship in scientist_authorships:
                    article = scientist_authorship.artifact
                    if article.id not in article_ids:
                        article_ids.append(article.id)
                        article_authorships = Authorship.objects.filter(artifact_id=article.id)
                        author_ids = []
                        for article_authorship in article_authorships:
                            author = article_authorship.author
                            if author.id not in author_ids:
                                author_ids.append(author.id)
                                if author.id != scientist_obj.id:
                                    if author.is_pi_inb:
                                        if author.id in inb_pi_collaborations.keys():
                                            inb_pi_collaborations[author.id]['num_collaborations'] += 1
                                            if article.year > inb_pi_collaborations[author.id]['year_last_collaboration']:
                                                inb_pi_collaborations[author.id]['year'] = article.year
                                        else:
                                            collaboration_dict = {
                                                'scientist_obj': author,
                                                'year_last_collaboration': article.year,
                                                'num_collaborations': 1
                                            }
                                            inb_pi_collaborations[author.id] = collaboration_dict
                inb_pi_collaborator = None
                for id, collaboration_info in inb_pi_collaborations.items():
                    if not inb_pi_collaborator:
                        inb_pi_collaborator = collaboration_info
                    else:
                        if collaboration_info['num_collaborations'] > inb_pi_collaborator['num_collaborations']:
                            inb_pi_collaborator = collaboration_info
                        elif collaboration_info['num_collaborations'] == inb_pi_collaborator['num_collaborations']:
                            if collaboration_info['year_last_collaboration'] > inb_pi_collaborator['year_last_collaboration']:
                                inb_pi_collaborator = collaboration_info
                if inb_pi_collaborator:
                    logger.info(f"The pi collaborator of {scientist_obj.first_name + ' ' + scientist_obj.last_name} is "
                                 f"{inb_pi_collaborator['scientist_obj'].first_name + ' ' +  inb_pi_collaborator['scientist_obj'].last_name}")
                    scientist_obj.most_recent_pi_inb_collaborator = inb_pi_collaborator['scientist_obj']
                    scientist_obj.save()

    def check_scientist_authorship(self, request, queryset):
        num_scientists_without_authorship = 0
        for scientist_obj in queryset:
            scientist_authorships = Authorship.objects.filter(author_id=scientist_obj.id)
            if not scientist_authorships:
                num_scientists_without_authorship += 1
                logger.info(f"The scientist {scientist_obj.id} doesn't have authorship")
        msg = f"Out of the {len(queryset)} scientists selected, " \
              f"{num_scientists_without_authorship} do not have authorship"
        self.message_user(request, msg, level=messages.SUCCESS)
    check_scientist_authorship.short_description = 'Check authorship of scientists'

    def __get_co_authors(self, authors, article_mgm, create_authors_dont_exist=False):
        paper_scientists = []
        inb_pi_within_author_list = None
        for author in authors:
            if 'ForeName' in author.keys():
                try:
                    author_obj = Scientist.objects.get(
                        first_name__iexact=author['ForeName'],
                        last_name__iexact=author['LastName']
                    )
                    if author_obj.is_pi_inb:
                        inb_pi_within_author_list = author_obj
                    paper_scientists.append(author_obj)
                except Scientist.DoesNotExist:
                    if create_authors_dont_exist:
                        paper_scientists.append(article_mgm.create_update_scientist(author))
        return paper_scientists, inb_pi_within_author_list

    def complete_authorship_of_scientists(self, request, queryset):
        ec = EntrezClient()
        am = ArticleMgm()
        scientists_without_authorship = 0
        new_authorship = 0
        for scientist_obj in queryset:
            scientist_authorships = Authorship.objects.filter(author_id=scientist_obj.id)
            if not scientist_authorships:
                scientists_without_authorship += 1
                scientist_name = scientist_obj.first_name + ' ' + scientist_obj.last_name
                logger.info(f"Getting articles of {scientist_name}")
                results = ec.search(f"{scientist_name}[author]", use_history=False, batch_size=500)
                if len(results['IdList']) > 0:
                    papers = ec.fetch_in_bulk_from_list(results['IdList'])
                    for i, paper in enumerate(papers):
                        paper_authors = paper['MedlineCitation']['Article']['AuthorList']
                        paper_doi = am.get_paper_doi(paper)
                        try:
                            if paper_doi:
                                article_obj = Article.objects.get(doi=paper_doi)
                            else:
                                article_obj = Article.objects.get(repo_id__value=str(paper['MedlineCitation']['PMID']))
                            co_authors, _ = self.__get_co_authors(paper_authors, am, True)
                            total_authors = len(co_authors)
                            logger.info(f"Saving authorship of {scientist_name}")
                            for index, co_author in enumerate(co_authors):
                                authorship_objs = Authorship.objects.filter(author=co_author, artifact=article_obj)
                                if len(authorship_objs) == 0:
                                    am.create_update_authorship(co_author, index, total_authors, article_obj)
                                    new_authorship += 1
                                    logger.info(f"New authorship created!")
                                    co_author.articles += 1
                                    if index == 0:
                                        co_author.articles_as_first_author += 1
                                    if index == total_authors-1:
                                        co_author.articles_as_last_author += 1
                                    co_author.save()
                        except Article.DoesNotExist:
                            _, inb_pi_within_authors = self.__get_co_authors(paper_authors, am)
                            if inb_pi_within_authors:
                                logger.info(f"Found a paper that doesn't exist in the database but has the INB PI "
                                             f"{inb_pi_within_authors.last_name + ' ' + inb_pi_within_authors.first_name} "
                                             f"as one of the authors")
                                am.process_paper(i, paper)
        msg = f"{new_authorship} new authorship were created for the {scientists_without_authorship} scientists without " \
              f"authorship"
        self.message_user(request, msg, level=messages.SUCCESS)
    complete_authorship_of_scientists.short_description = 'Complete authorship of scientists'

    def identify_possible_duplicates(self, request, queryset):
        jarowinkler = JaroWinkler()
        all_scientists = Scientist.objects.order_by('last_name')
        min_score_last_name_similarity = 0.95
        min_score_first_name_similarity = 0.75
        logger.info("Detecting possible duplicates, it might take some time, please wait...")
        for scientist_obj in queryset:
            if scientist_obj.possible_duplicate:
                continue
            transformed_last_name_sobj = normalize_transform_text(scientist_obj.last_name.lower())
            for scientist_obj_in_all in all_scientists:
                if scientist_obj_in_all.id == scientist_obj.id:
                    continue
                transformed_last_name_sobjall = normalize_transform_text(scientist_obj_in_all.last_name.lower())
                # compare only against last names that start with the same letter
                if transformed_last_name_sobj[0] == transformed_last_name_sobjall[0]:
                    # compute similarity of last names
                    last_name_similarity_score = jarowinkler.similarity(transformed_last_name_sobj,
                                                                        transformed_last_name_sobjall)
                    if last_name_similarity_score >= min_score_last_name_similarity:
                        # compute similarity of first names
                        transformed_first_name_sobj = normalize_transform_text(scientist_obj.first_name.lower())
                        transformed_first_name_sobjall = normalize_transform_text(scientist_obj_in_all.first_name.lower())
                        first_name_similarity_score = jarowinkler.similarity(transformed_first_name_sobj,
                                                                             transformed_first_name_sobjall)
                        if first_name_similarity_score >= min_score_first_name_similarity:
                            if not scientist_obj.possible_duplicate:
                                scientist_obj.possible_duplicate = True
                                scientist_obj.save()
                            scientist_obj_in_all.possible_duplicate = True
                            scientist_obj_in_all.save()
                else:
                    if transformed_last_name_sobj[0] < transformed_last_name_sobjall[0]:
                        break
        possible_duplicates = Scientist.objects.filter(possible_duplicate=True).count()
        msg = f"{possible_duplicates} possible duplicates were identified"
        self.message_user(request, msg, level=messages.SUCCESS)
    identify_possible_duplicates.short_description = 'Identify possible duplicates'

    def mark_as_not_duplicate(self, request, queryset):
        for scientist_obj in queryset:
            scientist_obj.possible_duplicate = False
            scientist_obj.save()
        msg = f"{len(queryset)} records were marked as not duplicates"
        self.message_user(request, msg, level=messages.SUCCESS)
    mark_as_not_duplicate.short_description = 'Remove from duplicates list'

    def udpate_productivity_metrics(self, request, queryset):
        scientist_ids = []
        for scientist_obj in queryset:
            scientist_ids.append(scientist_obj.id)
        update_productivy_metrics.delay(scientist_ids)
        msg = f"Records are being updated, please check the log to follow updates on the process"
        self.message_user(request, msg, level=messages.SUCCESS)
    udpate_productivity_metrics.short_description = 'Update productivity metrics'

    def compute_h_index(self, request, queryset):
        scientist_ids = []
        for scientist_obj in queryset:
            scientist_ids.append(scientist_obj.id)
        compute_h_index.delay(scientist_ids)
        msg = f"The computation has started, please check the log to follow updates on the process"
        self.message_user(request, msg, level=messages.SUCCESS)
    compute_h_index.short_description = 'Compute h-index'

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    ordering = ('name', 'country')
    search_fields = ('name', 'country__name')


@admin.register(Affiliation)
class AffiliationAdmin(admin.ModelAdmin):
    list_display = ('scientist', 'institution', 'joined_date')
    actions = ['fill_join_date', 'remove_duplicated_affiliation']
    search_fields = ('scientist', 'institution')

    def fill_join_date(self, request, queryset):
        affiliation_ids = []
        for affiliation in queryset:
            affiliation_ids.append(affiliation.id)
        fill_affiliation_join_date.delay(affiliation_ids)
        msg = f"The process has started, please refer to the log files for updates on the process"
        self.message_user(request, msg, level=messages.SUCCESS)
    fill_join_date.short_description = 'Complete affiliation join date'

    def remove_duplicated_affiliation(self, request, queryset):
        affiliations = Affiliation.objects.all()
        unique_affiliations = {}
        num_duplicates = 0
        for affiliation in affiliations:
            scientist_institution = (affiliation.scientist.id, affiliation.institution.id)
            if scientist_institution not in unique_affiliations.keys():
                unique_affiliations[scientist_institution] = affiliation.id
            else:
                logger.info(f"Removing the duplicate of scientist {affiliation.scientist} and "
                             f"institution {affiliation.institution}")
                num_duplicates += 1
                existing_affiliation = Affiliation.objects.get(id=unique_affiliations[scientist_institution])
                if existing_affiliation.id > affiliation.id:
                    affiliation.articles += existing_affiliation.articles
                    affiliation.save()
                    existing_affiliation.delete()
                    unique_affiliations[scientist_institution] = affiliation.id
                else:
                    existing_affiliation.articles += affiliation.articles
                    existing_affiliation.save()
                    affiliation.delete()
        msg = f"It was removed {num_duplicates} duplicated affiliations"
        self.message_user(request, msg, level=messages.SUCCESS)
    remove_duplicated_affiliation.short_description = 'Remove duplicates'


class YearFilter(MultipleChoiceListFilter):
    title = 'Year'
    parameter_name = 'year__in'

    def lookups(self, request, model_admin):
        year_objs =  Article.objects.values('year').distinct().order_by('year')
        years = []
        for year_obj in year_objs:
            years.append((year_obj['year'], str(year_obj['year'])))
        return tuple(years)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'doi', 'authors', 'num_citations', 'num_references', 'url')
    ordering = ('year', 'title',)
    search_fields = ('title', 'doi')
    list_filter = (YearFilter, 'inb_pi_as_author')
    actions = ['export_articles_to_csv', 'get_citations', 'get_references', 'identify_self_citations',
               'mark_articles_of_inb_pis']

    def authors(self, obj):
        authorships = Authorship.objects.filter(artifact=obj)
        authors = []
        author_ids = []
        for authorship in authorships:
            author = authorship.author
            author_name = author.first_name + ' ' + author.last_name
            if author.id not in author_ids:
                author_ids.append(author.id)
                authors.append(author_name)
        return ', '.join(list(authors))

    def num_citations(self, obj):
        return ArtifactCitation.objects.filter(to_artifact=obj).count()
    num_citations.short_description = 'Citations'

    def num_references(self, obj):
        return ArtifactCitation.objects.filter(from_artifact=obj).count()
    num_references.short_description = 'References'

    def export_articles_to_csv(self, request, queryset):
        filename = 'articles.csv'
        logger.info(f"Exporting {len(queryset)} articles")
        with open('articles.csv', 'w', encoding='utf-8') as f:
            headers = ['title', 'year', 'doi']
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for article_obj in queryset:
                article_dict = {
                    'title': article_obj.title,
                    'year': article_obj.year,
                    'doi': article_obj.doi
                }
                writer.writerow(article_dict)
        msg = f"The information of {len(queryset)} articles were successfully exported to the file {filename}"
        self.message_user(request, msg, level=messages.SUCCESS)
    export_articles_to_csv.short_description = 'Export articles information'

    def get_citations(self, request, queryset):
        article_ids = []
        for article in queryset:
            article_ids.append(article.id)
        get_citations.delay(article_ids)
        msg = f"The process of collecting citations has started, please refer to the log to get updates about it"
        self.message_user(request, msg, level=messages.SUCCESS)
    get_citations.short_description = 'Get citations'

    def get_references(self, request, queryset):
        article_ids = []
        for article in queryset:
            article_ids.append(article.id)
        get_references.delay(article_ids)
        msg = f"The process of collecting references has started, please refer to the log to get updates about it"
        self.message_user(request, msg, level=messages.SUCCESS)
    get_references.short_description = 'Get references'

    def mark_articles_of_inb_pis(self, request, queryset):
        article_ids = []
        for article in queryset:
            article_ids.append(article.id)
        mark_articles_of_inb_pis.delay(article_ids)
        msg = f"The process has started, please refer to the log to get updates about it"
        self.message_user(request, msg, level=messages.SUCCESS)
    mark_articles_of_inb_pis.short_description = "Mark INB PIs' articles"

    def identify_self_citations(self, request, queryset):
        article_ids = []
        for article in queryset:
            article_ids.append(article.id)
        identify_self_citation.delay(article_ids)
        msg = f"The process has started, please refer to the log to get updates about it"
        self.message_user(request, msg, level=messages.SUCCESS)
    identify_self_citations.short_description = "Identify self-citations"


@admin.register(Authorship)
class AuthorshipAdmin(admin.ModelAdmin):
    list_display = ('author', 'artifact', 'first_author')
    ordering = ('author', 'artifact')
    search_fields = ('author__first_name', 'author__last_name', 'artifact__title')

    def get_queryset(self, request):
        qs = super().get_queryset(request) #super(AuthorshipAdmin, self).queryset(request)
        qs = qs.distinct('author', 'artifact')
        return qs


@admin.register(Network)
class NetworkAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'num_nodes', 'num_edges')
    ordering = ('name',)
    actions = ['export_network_into_gefx_format']

    def num_nodes(self, obj):
        return NetworkNode.objects.filter(network=obj).count()
    num_nodes.short_description = 'Number of Nodes'

    def num_edges(self, obj):
        return NetworkEdge.objects.filter(network=obj).count()
    num_edges.short_description = 'Number of Edges'

    def __convert_model_date_type_to_gefx_type(self, data_type):
        if data_type == 'int':
            return 'integer'
        elif data_type == 'bool':
            return 'boolean'
        elif data_type == 'float':
            return 'float'
        else:
            return 'string'

    def export_network_into_gefx_format(self, request, queryset):
        for network_obj in queryset:
            file_name = network_obj.name + '__' + network_obj.date.strftime('%m%d%Y%H%M%S') + '.gexf'
            f_name = pathlib.Path(__file__).parents[1].joinpath('sna', 'gexf', file_name)

            with open(str(f_name), 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<gexf xmlns="http://www.gexf.net/1.2draft" xmlns:viz="http://www.gexf.net/1.1draft/viz" '
                        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                        'xsi:schemaLocation="http://www.gexf.net/1.2draft http://www.gexf.net/1.2draft/gexf.xsd" '
                        'version="1.2">\n')
                f.write('<meta lastmodifieddate="{0}">\n'.format(network_obj.date))
                f.write('<creator>ImpactApp (BSC)</creator>\n')
                f.write('<description>{0}</description>\n'.format(network_obj.name))
                f.write('</meta>\n')
                f.write('<graph mode="static" defaultedgetype="{0}">\n'.format(network_obj.type))
                # add data attributes
                f.write('<attributes class="node">\n')
                network_nodes = NetworkNode.objects.filter(network=network_obj)
                list_attrs = []
                for attr_index, attr in enumerate(network_nodes[0].attrs.all()):
                    attr_type = self.__convert_model_date_type_to_gefx_type(attr.type)
                    f.write('<attribute id="{0}" title="{1}" type="{2}"/>\n'.format(attr_index, attr.name, attr_type))
                    list_attrs.append(attr.name)
                f.write('</attributes>\n')
                # add nodes
                f.write('<nodes>\n')
                list_nodes = []
                for index_node, node in enumerate(network_nodes):
                    f.write('<node id="{0}" label="{1}">\n'.format(index_node, node.name))
                    f.write('<attvalues>\n')
                    for attr in node.attrs.all():
                        index_attr = list_attrs.index(attr.name)
                        f.write('<attvalue for="{0}" value="{1}"/>\n'.format(index_attr, attr.value))
                    f.write('</attvalues>\n')
                    #f.write('<viz:size value="{0}"/>\n'.format(node['ff_ratio']))
                    f.write('</node>\n')
                    list_nodes.append(node.name)
                f.write('</nodes>\n')
                # add edges
                f.write('<edges>\n')
                network_edges = NetworkEdge.objects.filter(network=network_obj)
                for index_edge, edge in enumerate(network_edges):
                    id_vertexA = list_nodes.index(edge.node_a.name)
                    id_vertexB = list_nodes.index(edge.node_b.name)
                    weight = edge.attrs.all()[0].value
                    f.write('<edge id="{0}" source="{1}" target="{2}" weight="{3}" label="{4}"/>\n'.
                            format(index_edge, id_vertexA, id_vertexB, weight, weight))
                f.write('</edges>\n')
                f.write('</graph>\n')
                f.write('</gexf>\n')
        msg = f"The collaboration network was exported successfully"
        self.message_user(request, msg, level=messages.SUCCESS)


@admin.register(Impact)
class ImpactAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'start_year', 'end_year', 'total_publications', 'total_w_impact')
    readonly_fields = ('date', 'total_publications', 'total_weighted_impact')
    actions = ['compute_sci_impact_inb']

    def compute_sci_impact_inb(self, request, queryset):
        for obj in queryset:
            total_publications, total_weighted_impact = 0, 0
            arr_impact_details = []
            for year in range(obj.start_year, obj.end_year + 1):
                field_citations_year_obj = FieldCitations.objects.get(year=year)
                field_citations = field_citations_year_obj.avg_citations_field
                publications_year = Article.objects.filter(year=year, inb_pi_as_author=True)
                num_publications_year = len(publications_year)
                total_publications += num_publications_year
                num_citations = 0
                num_not_cited_publications = 0
                num_self_citations = 0
                for publication in publications_year:
                    citations = ArtifactCitation.objects.filter(to_artifact=publication)
                    if len(citations) > 0:
                        num_citations += len(citations)
                        for citation in citations:
                            if citation.self_citation:
                                num_self_citations += 1
                    else:
                        num_not_cited_publications += 1
                avg_cpp = num_citations / num_publications_year
                prop_ncp = num_not_cited_publications / num_publications_year
                prop_sc = num_self_citations / num_citations
                impact_field = avg_cpp / field_citations
                impact_details_dict = {
                    'impact_header': obj,
                    'year': year,
                    'publications': num_publications_year,
                    'citations': num_citations,
                    'avg_citations_per_publication': avg_cpp,
                    'prop_not_cited_publications': prop_ncp,
                    'prop_self_citations': prop_sc,
                    'impact_field': impact_field
                }
                arr_impact_details.append(impact_details_dict)
            for impact_details in arr_impact_details:
                prop_py = impact_details['publications'] / total_publications
                impact_details['prop_publications_year'] = prop_py
                weighted_if = impact_details['impact_field'] * prop_py
                impact_details['weighted_impact_field'] = weighted_if
                total_weighted_impact += weighted_if
                id_obj = ImpactDetail(**impact_details)
                id_obj.save()
            obj.total_publications = total_publications
            obj.total_weighted_impact = total_weighted_impact
            obj.save()
        msg = f"The computation of the scientific impact was computed successfully!"
        self.message_user(request, msg, level=messages.SUCCESS)
    compute_sci_impact_inb.short_description = 'Compute the Scientific Impact of the INB'

    def total_w_impact(self, obj):
        return round(obj.total_weighted_impact, 2)
    total_w_impact.short_description = 'Total Weighted Impact'


@admin.register(FieldCitations)
class FieldCitationsAdmin(admin.ModelAdmin):
    list_display = ('field', 'source_name', 'source_url', 'year', 'avg_citations_field')
    ordering = ('year',)


@admin.register(ImpactDetail)
class ImpactDetailAdmin(admin.ModelAdmin):
    list_display = ('impact_header', 'year', 'publications', 'citations', 'citations_per_publication',
                    'not_cited_publications', 'self_citations', 'citations_field', 'impact',
                    'publications_year', 'w_impact_field')
    ordering = ('year',)

    def citations_per_publication(self, obj):
        return round(obj.avg_citations_per_publication, 2)

    def not_cited_publications(self, obj):
        return round(100*obj.prop_not_cited_publications, 2)
    not_cited_publications.short_description = '% Not Cited Publications'

    def self_citations(self, obj):
        return round(100*obj.prop_self_citations, 2)
    self_citations.short_description = '% Self-citations'

    def impact(self, obj):
        return round(obj.impact_field, 2)
    impact.short_description = 'Scientific Impact'

    def citations_field(self, obj):
        fc = FieldCitations.objects.get(year=obj.year)
        return round(fc.avg_citations_field, 2)
    citations_field.short_description = 'Avg. Field Citations of the Year'

    def publications_year(self, obj):
        return round(100*obj.prop_publications_year, 2)
    publications_year.short_description = '% Publications of the Total'

    def w_impact_field(self, obj):
        return round(obj.weighted_impact_field, 2)
    w_impact_field.short_description = 'Weighted Impact Field'
