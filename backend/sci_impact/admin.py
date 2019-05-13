from collections import defaultdict
from data_collector.pubmed import EntrezClient
from data_collector.utils import get_gender, curate_text
from django_admin_multiple_choice_list_filter.list_filters import MultipleChoiceListFilter
from django.contrib import admin, messages
from django.db import IntegrityError, transaction
from sci_impact.models import Scientist, Country, Institution, Affiliation, Venue, Article, Authorship, CustomField

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
    list_display = ('last_name', 'first_name', 'gender', 'nationality')
    ordering = ('last_name', )
    search_fields = ('first_name', 'last_name',)
    actions = ['get_articles_pubmed']
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
            Authorship.objects.get(author=author_obj, artifact=article_obj)
            Authorship.objects.filter(author=author_obj, artifact=article_obj).update(**authorship_dict)
        except Authorship.DoesNotExist:
            authorship_obj = Authorship(**authorship_dict)
            authorship_obj.save()
            self.objs_created['Authorship'].append(authorship_obj)

    def get_articles_pubmed(self, request, queryset):
        ec = EntrezClient()
        for scientist_obj in queryset:
            scientist_name = scientist_obj.first_name + ' ' + scientist_obj.last_name
            logging.info(f"Getting articles of {scientist_name}")
            results = ec.search(f"{scientist_name}[author]")
            papers = ec.fetch_in_batch_from_history(results['Count'], results['WebEnv'], results['QueryKey'])
            for i, paper in enumerate(papers):
                paper_meta_data = paper['MedlineCitation']['Article']
                logging.info(f"[{i}] Processing paper {paper_meta_data['ArticleTitle']}")
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
                                        full_name = author['ForeName'] + ' ' + author['LastName']
                                        author_dict['gender'] = get_gender(full_name)
                                        author_obj = Scientist(**author_dict)
                                        author_obj.save()
                                        self.objs_created['Scientist'].append(author_obj)
                                    # Update scientists' publication metrics
                                    author_obj.articles += 1
                                    if index == 0:
                                        author_obj.articles_as_first_author += 1
                                    if index == (total_authors-1):
                                        author_obj.articles_as_last_author += 1
                                    author_obj.save()
                                    ###
                                    # Iterate over author's affiliations
                                    ###
                                    for affiliation_str in author['AffiliationInfo']:
                                        if affiliation_str['Affiliation']:
                                            affiliations = self.__get_affiliations(affiliation_str['Affiliation'])
                                            if len(affiliations) == 0:
                                                # the author does not have affiliations, let's create their
                                                # authorship anyways
                                                self.__create_update_authorship(author_obj, index, total_authors,
                                                                                article_obj)
                                                continue
                                        else:
                                            # affiliation does not exists, let's create the authorship anyways
                                            self.__create_update_authorship(author_obj, index, total_authors,
                                                                            article_obj)
                                            continue
                                        for institution in affiliations:
                                            ###
                                            # 5) Create/Retrieve institution
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
                                            self.__create_update_authorship(author_obj, index, total_authors,
                                                                            article_obj, institution_obj)
                    except IntegrityError as e:
                        # Transaction failed, log the error and continue with the paper
                        logging.error(e)
        self.__display_feedback_msg(request)
    get_articles_pubmed.short_description = 'Get articles (Source: PubMed)'


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
    list_filter = (YearFilter,)
    actions = ['export_articles_to_csv']

    def authors(self, obj):
        authorships = Authorship.objects.filter(artifact=obj)
        authors = []
        for authorship in authorships:
            author_name = authorship.author.first_name + ' ' + authorship.author.last_name
            authors.append(author_name)
        return ', '.join(authors)

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
