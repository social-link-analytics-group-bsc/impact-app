from collections import defaultdict
from data_collector.pubmed import EntrezClient
from data_collector.utils import get_gender, curate_text
from datetime import datetime
from django_admin_multiple_choice_list_filter.list_filters import MultipleChoiceListFilter
from django.contrib import admin, messages
from django.db import IntegrityError, transaction
from sci_impact.models import Scientist, Country, Institution, Affiliation, Venue, Article, Authorship, CustomField, \
                              Network, NetworkNode, NetworkEdge
from similarity.jarowinkler import JaroWinkler
from data_collector.utils import normalize_transform_text

import csv
import logging
import pathlib
import requests
import re

logging.basicConfig(filename=str(pathlib.Path(__file__).parents[1].joinpath('impact_app.log')),
                    level=logging.DEBUG)
logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)


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
            logging.info(f"Creating country: {country_name}")
            Country.objects.update_or_create(name=country_name, iso_code=country_iso_code,
                                             defaults={'alternative_names': alt_names_str})
    load_countries.short_description = 'Load list of countries'


@admin.register(Scientist)
class ScientistAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'gender', 'is_pi_inb', 'articles', 'articles_as_first_author',
                    'articles_as_last_author','articles_citations', 'total_citations')
    ordering = ('last_name', 'articles', 'articles_as_first_author', 'articles_as_last_author')
    search_fields = ('first_name', 'last_name',)
    actions = ['compute_coauthors_network', 'get_articles_pubmed', 'identify_possible_duplicates', 'mark_as_duplicate',
               'remove_duplicates', 'obtain_pi_collaborator', 'mark_as_not_duplicate', 'udpate_productivity_metrics']
    list_filter = ('is_pi_inb', )
    objs_created = defaultdict(list)
    countries = []
    regex = re.compile('[,;]+')

    def __load_countries(self):
        country_objs = Country.objects.all()
        for country_obj in country_objs:
            country_names = set()
            country_names.add(country_obj.name)
            for alt_country in country_obj.alternative_names.split(','):
                country_names.add(alt_country)
            self.countries.append({'names': list(country_names), 'iso_code': country_obj.iso_code})

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

    def __get_paper_doi(self, paper):
        if paper['PubmedData'].get('ArticleIdList'):
            for other_id in paper['PubmedData']['ArticleIdList']:
                if 'doi' in other_id.attributes.values():
                    return other_id.lower()
        return ''

    def __get_paper_url(self, paper_doi):
        BASE_URL = 'https://doi.org/'
        paper_doi_url = BASE_URL + paper_doi
        try:
            ret_rq = requests.get(paper_doi_url)
            if ret_rq.status_code == 200:
                return ret_rq.url
            else:
                return ''
        except Exception:
            return ''

    def __get_paper_keywords(self, paper_meta_data):
        keywords = paper_meta_data.get('KeywordList')
        if keywords:
            return ', '.join(keywords)
        else:
            return ''

    def __which_country(self, aff_str):
        for country_dict in self.countries:
            for country in country_dict['names']:
                if aff_str.lower().strip() == country.lower():
                    return country, country_dict['iso_code']
        return ''

    def __is_countryand_case(self, aff_str):
        aff_str = aff_str.lower().strip()
        for country_dict in self.countries:
            for country in country_dict['names']:
                country_and_case = country.lower() + ' and '
                if aff_str.find(country_and_case) == 0:
                    return country, country_dict['iso_code']
        return ''

    def __get_country_iso_code(self, institution_name):
        for country_dict in self.countries:
            for country in country_dict['names']:
                regex_country = re.compile(f", {country}$")
                if regex_country.search(institution_name):
                    return country_dict['iso_code']
        return ''

    def __get_affiliations(self, affiliation):
        affiliations = []
        current_affiliation = []
        if not self.countries:
            self.__load_countries()
        affiliation = curate_text(affiliation)
        aff_array = self.regex.split(affiliation)
        for aff in aff_array:
            found_country = self.__which_country(aff)
            if found_country:
                current_affiliation.append(found_country[0])
                affiliations.append({'name': ', '.join(current_affiliation), 'country_iso_code': found_country[1]})
                current_affiliation = []
            else:
                found_country = self.__is_countryand_case(aff)
                if found_country:
                    current_affiliation.append(found_country[0])
                    affiliations.append({'name': ', '.join(current_affiliation), 'country_iso_code': found_country[1]})
                    aff = aff[len(found_country + ' and '):]  # remove country name + and
                    current_affiliation = [aff.strip()]
                else:
                    current_affiliation.append(aff.strip())
        return affiliations

    def __create_update_venue(self, paper_meta_data, venue_meta_data):
        venue_dict = {'name': str(venue_meta_data['Title'])}
        if venue_meta_data.get('JournalIssue').get('Volume'):
            venue_dict['volume'] = str(venue_meta_data.get('JournalIssue').get('Volume'))
        if venue_meta_data.get('JournalIssue').get('Issue'):
            venue_dict['issue'] = str(venue_meta_data.get('JournalIssue').get('Issue'))
        if venue_meta_data.get('JournalIssue').get('PubDate').get('Year'):
            venue_dict['year'] = int(venue_meta_data.get('JournalIssue').get('PubDate').get('Year'))
        if venue_meta_data.get('ISSN'):
            venue_dict['issn'] = str(venue_meta_data.get('ISSN'))
        if venue_meta_data.get('JournalIssue').get('PubDate').get('Month'):
            venue_dict['month'] = str(venue_meta_data.get('JournalIssue').get('PubDate').get('Month'))
        if venue_meta_data.get('JournalIssue').get('PubDate').get('Day'):
            venue_dict['day'] = int(venue_meta_data.get('JournalIssue').get('PubDate').get('Day'))
        if str(paper_meta_data.get('PublicationTypeList')[0]) == 'Journal Article':
            venue_dict['type'] = 'journal'
        elif str(paper_meta_data.get('PublicationTypeList')[0]) == 'Conference Article':
            venue_dict['type'] = 'proceeding'
        else:
            venue_dict['type'] = 'other'
        try:
            venue_obj = Venue.objects.get(name__iexact=venue_dict['name'], type__exact=venue_dict['type'])
            Venue.objects.filter(name__iexact=venue_dict['name'], type__exact=venue_dict['type']).update(**venue_dict)
        except Venue.DoesNotExist:
            venue_obj = Venue(**venue_dict)
            venue_obj.save()
            self.objs_created['Venue'].append(venue_obj)
        return venue_obj

    def __create_update_article(self, paper, venue_obj, id_obj):
        paper_meta_data = paper['MedlineCitation']['Article']
        paper_doi = self.__get_paper_doi(paper)
        paper_keywords = self.__get_paper_keywords(paper['MedlineCitation']['Article'])
        paper_url = self.__get_paper_url(paper_doi) if paper_doi else ''
        article_dict = {
            'title': curate_text(paper_meta_data['ArticleTitle']),
            'doi': paper_doi,
            'academic_db': 'pubmed',
            'venue': venue_obj,
            'repo_ids': id_obj,
            'url': paper_url
        }
        if paper_meta_data.get('Language'):
            article_dict['language'] = str(paper_meta_data.get('Language')[0])
        if paper_meta_data.get('ArticleDate') and paper_meta_data.get('ArticleDate')[0].get('Year'):
            article_dict['year'] = int(paper_meta_data.get('ArticleDate')[0].get('Year'))
        elif paper['MedlineCitation'].get('DateCompleted'):
            article_dict['year'] = int(paper['MedlineCitation']['DateCompleted']['Year'])
        elif paper['MedlineCitation'].get('DateRevised'):
            article_dict['year'] = int(paper['MedlineCitation']['DateRevised']['Year'])
        else:
            raise Exception(f"Couldn't find the year of the article {article_dict['title']}")
        if paper_keywords:
            article_dict['keywords'] = paper_keywords
        article_obj = Article(**article_dict)
        article_obj.save()
        self.objs_created['Article'].append(article_obj)
        return article_obj

    def __create_update_authorship(self, author_obj, author_index, total_authors, article_obj, institution_obj=None):
        authorship_dict = {
            'author': author_obj,
            'artifact': article_obj,
            'first_author': author_index == 0,
            'last_author': author_index == (total_authors-1)
        }
        if institution_obj:
            authorship_dict['institution'] = institution_obj
        try:
            authorship_obj = Authorship.objects.get(author=author_obj, artifact=article_obj, institution=institution_obj)
            Authorship.objects.filter(author=author_obj, artifact=article_obj, institution=institution_obj).\
                update(**authorship_dict)
        except Authorship.DoesNotExist:
            authorship_obj = Authorship(**authorship_dict)
            authorship_obj.save()
            self.objs_created['Authorship'].append(authorship_obj)
        return authorship_obj

    def __create_update_scientist(self, author):
        author_dict = {
            'first_name': author['ForeName'],
            'last_name': author['LastName']
        }
        full_name = author['ForeName'] + ' ' + author['LastName']
        author_dict['gender'] = get_gender(full_name)
        author_obj = Scientist(**author_dict)
        author_obj.save()
        return author_obj

    def __process_paper(self, num_paper, paper):
        paper_meta_data = paper['MedlineCitation']['Article']
        logging.info(f"[{num_paper}] Processing paper {paper_meta_data['ArticleTitle']}")
        paper_doi = self.__get_paper_doi(paper)
        paper_pubmed_id = str(paper['MedlineCitation']['PMID'])
        try:
            if paper_doi:
                Article.objects.get(doi=paper_doi)
            else:
                Article.objects.get(repo_ids__value=paper_pubmed_id)
            logging.info(f"Paper already in the database!")
        except Article.DoesNotExist:
            venue_meta_data = paper['MedlineCitation']['Article']['Journal']
            try:
                with transaction.atomic():
                    ###
                    # 1) Create/Retrieve paper's venue
                    ###
                    venue_obj = self.__create_update_venue(paper_meta_data, venue_meta_data)
                    ###
                    # 2) Create/Retrieve pubmed id
                    ###
                    id_dict = {
                        'name': 'PubMed Id',
                        'value': paper_pubmed_id,
                        'type': 'str'
                    }
                    pubmed_id_obj, created = CustomField.objects.get_or_create(**id_dict)
                    if created: self.objs_created['CustomField'].append(pubmed_id_obj)
                    ###
                    # 3) Create/Retrieve paper
                    ###
                    article_obj = self.__create_update_article(paper, venue_obj, pubmed_id_obj)
                    ###
                    # Iterate over the paper's authors
                    ###
                    paper_authors = paper_meta_data['AuthorList']
                    total_authors = len(paper_authors)
                    for index, author in enumerate(paper_authors):
                        if 'ForeName' in author.keys():
                            ###
                            # 4) Create/Update author
                            ###
                            author_dict = {
                                'first_name': author['ForeName'],
                                'last_name': author['LastName']
                            }
                            try:
                                author_obj = Scientist.objects.get(
                                    first_name__iexact=author_dict['first_name'],
                                    last_name__iexact=author_dict['last_name']
                                )
                            except Scientist.DoesNotExist:
                                author_obj = self.__create_update_scientist(author)
                                self.objs_created['Scientist'].append(author_obj)
                            # Update scientists' publication metrics
                            author_obj.articles += 1
                            if index == 0:
                                author_obj.articles_as_first_author += 1
                            if index == (total_authors - 1):
                                author_obj.articles_as_last_author += 1
                            author_obj.save()
                            ###
                            # 5) Create/Retrieve article's authorship
                            ###
                            authorship_obj = self.__create_update_authorship(author_obj, index, total_authors,
                                                                             article_obj)
                            ###
                            # Iterate over author's affiliations
                            ###
                            for affiliation_str in author['AffiliationInfo']:
                                affiliations = []
                                if affiliation_str['Affiliation']:
                                    affiliations = self.__get_affiliations(affiliation_str['Affiliation'])
                                for institution in affiliations:
                                    ###
                                    # 6) Create/Retrieve institution
                                    ###
                                    institution_name = institution['name']
                                    institution_country_obj = Country.objects.get(
                                        iso_code=institution['country_iso_code'])
                                    try:
                                        institution_obj = Institution.objects.get(
                                            name__iexact=institution_name,
                                            country=institution_country_obj
                                        )
                                    except Institution.DoesNotExist:
                                        institution_obj = Institution(name=institution_name,
                                                                      country=institution_country_obj)
                                        institution_obj.save()
                                        self.objs_created['Institution'].append(institution_obj)
                                    ###
                                    # 7) Create/Retrieve author's affiliation
                                    ###
                                    affiliation_obj, created = Affiliation.objects.get_or_create(
                                        scientist=author_obj,
                                        institution=institution_obj
                                    )
                                    if created: self.objs_created['Institution'].append(affiliation_obj)
                                    # Update affiliation metrics
                                    affiliation_obj.articles += 1
                                    if index == 0:
                                        affiliation_obj.articles_as_first_author += 1
                                    affiliation_obj.save()
                                    ###
                                    # 8) Update authorship with institution
                                    ###
                                    authorship_obj.institution = institution_obj
                                    authorship_obj.save()
            except IntegrityError as e:
                # Transaction failed, log the error and continue with the paper
                logging.error(e)

    def get_articles_pubmed(self, request, queryset):
        ec = EntrezClient()
        for scientist_obj in queryset:
            scientist_name = scientist_obj.first_name + ' ' + scientist_obj.last_name
            logging.info(f"Getting articles of {scientist_name}")
            results = ec.search(f"{scientist_name}[author]")
            papers = ec.fetch_in_batch_from_history(results['Count'], results['WebEnv'], results['QueryKey'])
            for i, paper in enumerate(papers):
                self.__process_paper(i, paper)
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
            scientist_to_keep.articles_citations += duplicate_scientist.articles_citations
            scientist_to_keep.books += duplicate_scientist.books
            scientist_to_keep.patents += duplicate_scientist.patents
            scientist_to_keep.datasets += duplicate_scientist.datasets
            scientist_to_keep.tools += duplicate_scientist.tools
            scientist_to_keep.book_citations += duplicate_scientist.book_citations
            scientist_to_keep.dataset_citations += duplicate_scientist.dataset_citations
            scientist_to_keep.patent_citations += duplicate_scientist.patent_citations
            scientist_to_keep.tools_citations += duplicate_scientist.tools_citations
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

    def __insert_collaboration_edge(self, edge_tuple, edge_val, nodes_dict):
        node_a_obj = nodes_dict.get(edge_tuple[0])
        node_b_obj = nodes_dict.get(edge_tuple[1])
        edge = NetworkEdge(node_a=node_a_obj, node_b=node_b_obj, network=node_a_obj.network)
        edge.save()
        num_collaborations_attr = CustomField(name='num_collaborations', value=edge_val['num_collaborations'])
        num_collaborations_attr.save()
        edge.attrs.add(num_collaborations_attr)
        logging.info(f"Created a edge between {node_a_obj.name} and {node_b_obj.name}")

    def __insert_scientist_node(self, scientist_name, scientist_info, network_obj):
        node_obj = NetworkNode(name=scientist_name, network=network_obj)
        node_obj.save()
        for attr_name, attr_info in scientist_info.items():
            attr_obj = CustomField(name=attr_name, value=attr_info['value'], type=attr_info['type'])
            attr_obj.save()
            node_obj.attrs.add(attr_obj)
        logging.info(f"Inserted the node {scientist_name}")
        return node_obj

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
            logging.info(f"Created the scientist node {str(scientist_obj)}")
        return nodes

    def __create_update_edge(self, scientist_a, scientist_b, edges):
        edge_a = (str(scientist_a), str(scientist_b))
        edge_b = (str(scientist_b), str(scientist_a))
        edge = edges.get(edge_a)
        if edge:
            edge['num_collaborations'] += 1
        else:
            edge = edges.get(edge_b)
            if edge:
                edge['num_collaborations'] += 1
            else:
                edges[edge_a] = {
                    'num_collaborations': 1
                }
                logging.info(f"Created a edge between {str(scientist_a)} and {str(scientist_b)}")
        return edges

    def compute_coauthors_network(self, request, queryset):
        nodes, edges = {}, {}
        network_name = 'CollaborationNetwork'
        logging.info(f"Generating the network {network_name}, it might take some time...")
        net_obj = Network(name=network_name, date=datetime.now())
        if 'is_pi_inb__exact' in request.GET.keys():
            only_inb = True
            network_name += 'INB'
        else:
            only_inb = False
        # 0) Load to memory the data of the authorship table
        logging.info('Loading to memory the data of the authorship table')
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
            nodes = self.__create_scientist_node(scientist_obj, nodes)
            scientist_authorships = author_authorships.get(scientist_obj.id)
            article_ids = []
            for scientist_authorship in scientist_authorships:
                # iterate over the scientists' articles
                article = scientist_authorship.artifact
                if article.id not in article_ids:
                    article_ids.append(article.id)
                    scientist_article_authorships = article_authorships.get(article.id)
                    for scientist_article_authorship in scientist_article_authorships:
                        # iterate over the article's authors
                        author = scientist_article_authorship.author
                        if author.id != scientist_obj.id:
                            if only_inb:
                                if author.is_pi_inb:  # create only nodes and edges of INB PIs
                                    nodes = self.__create_scientist_node(scientist_obj, nodes)
                                    edges = self.__create_update_edge(scientist_obj, author, edges)
                            else:
                                nodes = self.__create_scientist_node(scientist_obj, nodes)
                                edges = self.__create_update_edge(scientist_obj, author, edges)
        # 2) Save record into the DB
        with transaction.atomic():
            net_obj.save()
            for node_name, node_info in nodes.items():
                self.__insert_scientist_node(node_name, node_info, net_obj)
            nodes_db = NetworkNode.objects.filter(network=net_obj)
            nodes_dict = {}
            for node_db in nodes_db:
                nodes_dict[node_db.name] = node_db
            for edge_tuple, edge_val in edges.items():
                self.__insert_collaboration_edge(edge_tuple, edge_val, nodes_dict)
        msg = f"The collaboration network was computed successfully"
        self.message_user(request, msg, level=messages.SUCCESS)
    compute_coauthors_network.short_description = 'Generate collaboration network'

    def obtain_pi_collaborator(self, request, queryset):
        for scientist_obj in queryset:
            logging.info(f"Obtaining the pi collaborator of {scientist_obj.first_name + ' ' + scientist_obj.last_name}")
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
                    logging.info(f"The pi collaborator of {scientist_obj.first_name + ' ' + scientist_obj.last_name} is "
                                 f"{inb_pi_collaborator['scientist_obj'].first_name + ' ' +  inb_pi_collaborator['scientist_obj'].last_name}")
                    scientist_obj.most_recent_pi_inb_collaborator = inb_pi_collaborator['scientist_obj']
                    scientist_obj.save()

    def check_scientist_authorship(self, request, queryset):
        num_scientists_without_authorship = 0
        for scientist_obj in queryset:
            scientist_authorships = Authorship.objects.filter(author_id=scientist_obj.id)
            if not scientist_authorships:
                num_scientists_without_authorship += 1
                logging.info(f"The scientist {scientist_obj.id} doesn't have authorship")
        msg = f"Out of the {len(queryset)} scientists selected, " \
              f"{num_scientists_without_authorship} do not have authorship"
        self.message_user(request, msg, level=messages.SUCCESS)
    check_scientist_authorship.short_description = 'Check authorship of scientists'

    def __get_co_authors(self, authors, create_authors_dont_exist=False):
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
                        paper_scientists.append(self.__create_update_scientist(author))
        return paper_scientists, inb_pi_within_author_list

    def complete_authorship_of_scientists(self, request, queryset):
        ec = EntrezClient()
        scientists_without_authorship = 0
        new_authorship = 0
        for scientist_obj in queryset:
            scientist_authorships = Authorship.objects.filter(author_id=scientist_obj.id)
            if not scientist_authorships:
                scientists_without_authorship += 1
                scientist_name = scientist_obj.first_name + ' ' + scientist_obj.last_name
                logging.info(f"Getting articles of {scientist_name}")
                results = ec.search(f"{scientist_name}[author]", use_history=False, batch_size=500)
                if len(results['IdList']) > 0:
                    papers = ec.fetch_in_bulk_from_list(results['IdList'])
                    for i, paper in enumerate(papers):
                        paper_authors = paper['MedlineCitation']['Article']['AuthorList']
                        paper_doi = self.__get_paper_doi(paper)
                        try:
                            if paper_doi:
                                article_obj = Article.objects.get(doi=paper_doi)
                            else:
                                article_obj = Article.objects.get(repo_ids__value=str(paper['MedlineCitation']['PMID']))
                            co_authors, _ = self.__get_co_authors(paper_authors, True)
                            total_authors = len(co_authors)
                            logging.info(f"Saving authorship of {scientist_name}")
                            for index, co_author in enumerate(co_authors):
                                authorship_objs = Authorship.objects.filter(author=co_author, artifact=article_obj)
                                if len(authorship_objs) == 0:
                                    self.__create_update_authorship(co_author, index, total_authors, article_obj)
                                    new_authorship += 1
                                    logging.info(f"New authorship created!")
                                    co_author.articles += 1
                                    if index == 0:
                                        co_author.articles_as_first_author += 1
                                    if index == total_authors-1:
                                        co_author.articles_as_last_author += 1
                                    co_author.save()
                        except Article.DoesNotExist:
                            _, inb_pi_within_authors = self.__get_co_authors(paper_authors)
                            if inb_pi_within_authors:
                                logging.info(f"Found a paper that doesn't exist in the database but has the INB PI "
                                             f"{inb_pi_within_authors.last_name + ' ' + inb_pi_within_authors.first_name} "
                                             f"as one of the authors")
                                self.__process_paper(i, paper)
        msg = f"{new_authorship} new authorship were created for the {scientists_without_authorship} scientists without " \
              f"authorship"
        self.message_user(request, msg, level=messages.SUCCESS)
    complete_authorship_of_scientists.short_description = 'Complete authorship of scientists'

    def identify_possible_duplicates(self, request, queryset):
        jarowinkler = JaroWinkler()
        all_scientists = Scientist.objects.order_by('last_name')
        min_score_last_name_similarity = 0.95
        min_score_first_name_similarity = 0.75
        logging.info("Detecting possible duplicates, it might take some time, please wait...")
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
        for scientist_obj in queryset:
            scientist_production = {'articles': 0, 'articles_as_first_author': 0, 'articles_as_last_author': 0}
            articles = []
            logging.info(f"Updating the metrics of {scientist_obj.first_name + '' + scientist_obj.last_name}")
            scientist_authorships = Authorship.objects.filter(author_id=scientist_obj.id)
            for scientist_authorship in scientist_authorships:
                if scientist_authorship.artifact_id not in articles:
                    articles.append(scientist_authorship.artifact_id)
                    scientist_production['articles'] += 1
                    if scientist_authorship.first_author:
                        scientist_production['articles_as_first_author'] += 1
                    if scientist_authorship.last_author:
                        scientist_production['articles_as_last_author'] += 1
            scientist_obj.articles = scientist_production['articles']
            scientist_obj.articles_as_first_author = scientist_production['articles_as_first_author']
            scientist_obj.articles_as_last_author = scientist_production['articles_as_last_author']
            scientist_obj.save()
        msg = f"{len(queryset)} records were updated"
        self.message_user(request, msg, level=messages.SUCCESS)
    udpate_productivity_metrics.short_description = 'Update productivity metrics'


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    ordering = ('name', 'country')
    search_fields = ('name', 'country__name')

@admin.register(Affiliation)
class AffiliationAdmin(admin.ModelAdmin):
    list_display = ('scientist', 'institution', 'joined_date')


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
    list_display = ('title', 'year', 'doi', 'authors', 'url')
    ordering = ('year', 'title')
    search_fields = ('title', 'doi')
    list_filter = (YearFilter, )
    actions = ['export_articles_to_csv']

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

    def export_articles_to_csv(self, request, queryset):
        filename = 'articles.csv'
        logging.info(f"Exporting {len(queryset)} articles")
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


@admin.register(Network)
class NetworkAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'num_nodes', 'num_edges')
    ordering = ('name',)
    actions = ['export_network_into_gefx_format']

    def num_nodes(self, obj):
        nodes = NetworkNode.objects.filter(network=obj)
        return len(nodes)
    num_nodes.short_description = 'Number of Nodes'

    def num_edges(self, obj):
        edges = NetworkEdge.objects.filter(network=obj)
        return len(edges)
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
            file_name = network_obj.name + '__' + str(network_obj.date) + '.gexf'
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