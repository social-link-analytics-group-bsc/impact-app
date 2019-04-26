from collections import defaultdict
from data_collector.pubmed import EntrezClient
from data_collector.utils import get_gender, curate_text
from django.contrib import admin, messages
from django.db import IntegrityError, transaction
from sci_impact.models import Scientist, Country, Institution, City, Region, Affiliation, Venue, Article, Authorship, \
                              CustomField

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
        with open(str('sci_impact/data/country_list.txt'), 'r') as f:
            for _, line in enumerate(f):
                line = line.split(':')
                country_name = line[1].replace('\n', '')
                country_code = line[0].replace('\n', '')
                Country.objects.get_or_create(name=country_name, iso_code=country_code)
    load_countries.short_description = 'Load list of countries'


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'country', 'wikipage')


@admin.register(Scientist)
class ScientistAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'gender', 'nationality')
    ordering = ('last_name', )
    search_fields = ('first_name', 'last_name',)
    actions = ['get_articles']
    objs_created = defaultdict(list)

    def __display_feedback_msg(self, request):
        if self.objs_created:
            msg = 'The action was completed successfully!\n'
            for model, objs in self.objs_created.items():
                msg += f"- It was created {model} objects of the type {len(objs)}\n"
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

    def __get_paper_url(self, paper_doi):
        BASE_URL = 'https://doi.org/'
        paper_doi_url = BASE_URL + paper_doi
        try:
            ret_rq = requests.get(paper_doi_url)
            if ret_rq.status_code == 200:
                return ret_rq.url
            else:
                return ''
        except requests.ConnectionError:
            return ''

    def __get_paper_keywords(self, paper_meta_data):
        keywords = paper_meta_data.get('KeywordList')
        if keywords:
            return ', '.join(keywords)
        else:
            return ''

    def __get_institution_country(self, institution_name):
        found_countries = []
        countries = Country.objects.all()
        for country in countries:
            regex_country = re.compile(f", {country.name}$")
            if regex_country.search(institution_name):
                found_countries.append(country)
        if found_countries:
            if len(found_countries) > 1:
                logging.warning(f"Found more than one country in the affiliation {', '.join(found_countries)}. "
                                f"Returning the first one")
            return found_countries[0]
        else:
            return None

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
        paper_url = self.__get_paper_url(paper_doi)
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

    def get_articles(self, request, queryset):
        ec = EntrezClient()
        for scientist_obj in queryset:
            scientist_name = scientist_obj.first_name + ' ' + scientist_obj.last_name
            logging.info(f"Getting articles of {scientist_name}")
            results = ec.search(f"{scientist_name}[author]")
            papers = ec.fetch_in_batch_from_history(results['Count'], results['WebEnv'], results['QueryKey'])
            for i, paper in enumerate(papers):
                paper_doi = self.__get_paper_doi(paper)
                try:
                    Article.objects.get(doi=paper_doi)
                except:
                    paper_meta_data = paper['MedlineCitation']['Article']
                    venue_meta_data = paper['MedlineCitation']['Article']['Journal']
                    logging.info(f"Found the paper: {paper_meta_data['ArticleTitle']}")
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
                                'value': str(paper['MedlineCitation']['PMID']),
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
                                        full_name = author['ForeName'] + ' ' + author['LastName']
                                        author_dict['gender'] = get_gender(full_name)
                                        author_obj = Scientist(**author_dict)
                                        author_obj.save()
                                        self.objs_created['Scientist'].append(author_obj)
                                    # Update scientists' publication metrics
                                    author_obj.articles += 1
                                    if index == 0:
                                        author_obj.articles_as_first_author += 1
                                    author_obj.save()
                                    ###
                                    # Iterate over author's affiliations
                                    ###
                                    for affiliation_str in author['AffiliationInfo']:
                                        for affiliation_name in affiliation_str['Affiliation'].split(';'):
                                            ###
                                            # 5) Create/Retrieve institution
                                            ###
                                            institution_name = curate_text(affiliation_name)
                                            institution_country_obj = self.__get_institution_country(institution_name)
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
                                            # 6) Create/Retrieve author's affiliation
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
                                            # 7) Create/Retrieve article's authorship
                                            ###
                                            authorship_dict = {
                                                'author': author_obj,
                                                'artifact': article_obj,
                                                'institution': institution_obj,
                                                'first_author': index == 0
                                            }
                                            authorship_obj, created = Authorship.objects.get_or_create(**authorship_dict)
                                            if created: self.objs_created['Authorship'].append(authorship_obj)
                    except IntegrityError as e:
                        # Transaction failed, log the error and continue with the paper
                        logging.error(e)
        self.__display_feedback_msg(request)
    get_articles.short_description = 'Get articles (PubMed)'


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'city', 'web_page')


@admin.register(Affiliation)
class AffiliationAdmin(admin.ModelAdmin):
    list_display = ('scientist', 'institution', 'joined_date')
