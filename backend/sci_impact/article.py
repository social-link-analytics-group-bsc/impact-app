from django.db import IntegrityError, transaction
from sci_impact.models import Affiliation, Article, Authorship, Country, CustomField, Institution, Scientist, Venue
from data_collector.utils import get_gender, curate_text

import logging
import pathlib
import requests
import re


logging.basicConfig(filename=str(pathlib.Path(__file__).parents[1].joinpath('impact_app.log')),
                    level=logging.DEBUG)
logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)


class ArticleMgm:

    __countries = []

    def __init__(self):
        self.__load_countries()

    def __load_countries(self):
        country_objs = Country.objects.all()
        for country_obj in country_objs:
            country_names = set()
            country_names.add(country_obj.name)
            for alt_country in country_obj.alternative_names.split(','):
                country_names.add(alt_country)
            self.__countries.append({'names': list(country_names), 'iso_code': country_obj.iso_code})

    def create_update_venue(self, paper_meta_data, venue_meta_data):
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
            return venue_obj, False
        except Venue.DoesNotExist:
            venue_obj = Venue(**venue_dict)
            venue_obj.save()
            return venue_obj, True

    def get_paper_doi(self, paper):
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

    def create_update_article(self, paper, venue_obj, id_obj):
        paper_meta_data = paper['MedlineCitation']['Article']
        paper_doi = self.get_paper_doi(paper)
        paper_keywords = self.__get_paper_keywords(paper['MedlineCitation']['Article'])
        paper_url = self.__get_paper_url(paper_doi) if paper_doi else ''
        article_dict = {
            'title': curate_text(paper_meta_data['ArticleTitle']),
            'doi': paper_doi,
            'academic_db': 'pubmed',
            'venue': venue_obj,
            'repo_id': id_obj,
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
        return article_obj, True

    def create_update_authorship(self, author_obj, author_index, total_authors, article_obj, institution_obj=None):
        authorship_dict = {
            'author': author_obj,
            'artifact': article_obj,
            'first_author': author_index == 0,
            'last_author': author_index == (total_authors - 1)
        }
        if institution_obj:
            authorship_dict['institution'] = institution_obj
        try:
            authorship_obj = Authorship.objects.get(author=author_obj, artifact=article_obj, institution=institution_obj)
            Authorship.objects.filter(author=author_obj, artifact=article_obj, institution=institution_obj). \
                update(**authorship_dict)
            return authorship_obj, False
        except Authorship.DoesNotExist:
            authorship_obj = Authorship(**authorship_dict)
            authorship_obj.save()
            return authorship_obj, True

    def create_update_scientist(self, author):
        author_dict = {
            'first_name': author['ForeName'],
            'last_name': author['LastName']
        }
        full_name = author['ForeName'] + ' ' + author['LastName']
        author_dict['gender'] = get_gender(full_name)
        author_obj = Scientist(**author_dict)
        author_obj.save()
        return author_obj

    def __which_country(self, aff_str):
        for country_dict in self.__countries:
            for country in country_dict['names']:
                if aff_str.lower().strip() == country.lower():
                    return country, country_dict['iso_code']
        return ''

    def __is_countryand_case(self, aff_str):
        aff_str = aff_str.lower().strip()
        for country_dict in self.__countries:
            for country in country_dict['names']:
                country_and_case = country.lower() + ' and '
                if aff_str.find(country_and_case) == 0:
                    return country, country_dict['iso_code']
        return ''

    def __get_affiliations(self, affiliation):
        regex = re.compile('[,;]+')
        affiliations = []
        current_affiliation = []
        affiliation = curate_text(affiliation)
        aff_array = regex.split(affiliation)
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

    def process_paper(self, num_paper, paper):
        article_obj = None
        created_objs = {}
        paper_meta_data = paper['MedlineCitation']['Article']
        logging.info(f"[{num_paper}] Processing paper {paper_meta_data['ArticleTitle']}")
        paper_doi = self.get_paper_doi(paper)
        paper_pubmed_id = str(paper['MedlineCitation']['PMID'])
        try:
            if paper_doi:
                article_obj = Article.objects.get(doi=paper_doi)
            else:
                article_obj = Article.objects.get(repo_id__value=paper_pubmed_id)
            logging.info(f"Paper already in the database!")
            return article_obj, None
        except Article.DoesNotExist:
            venue_meta_data = paper['MedlineCitation']['Article']['Journal']
            try:
                with transaction.atomic():
                    ###
                    # 1) Create/Retrieve paper's venue
                    ###
                    venue_obj, created = self.create_update_venue(paper_meta_data, venue_meta_data)
                    if created:
                        created_objs['Venue'] = venue_obj
                    ###
                    # 2) Create/Retrieve pubmed id
                    ###
                    id_dict = {
                        'name': 'PubMed Id',
                        'value': paper_pubmed_id,
                        'type': 'str'
                    }
                    pubmed_id_obj, created = CustomField.objects.get_or_create(**id_dict)
                    if created:
                        created_objs['CustomField'] = pubmed_id_obj
                    ###
                    # 3) Create/Retrieve paper
                    ###
                    article_obj, created = self.create_update_article(paper, venue_obj, pubmed_id_obj)
                    if created:
                        created_objs['Article'] = article_obj
                    ###
                    # Iterate over the paper's authors
                    ###
                    paper_authors = paper_meta_data['AuthorList']
                    total_authors = len(paper_authors)
                    created_objs['Scientist'] = []
                    created_objs['Authorship'] = []
                    created_objs['Institution'] = []
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
                                author_obj = self.create_update_scientist(author)
                                created_objs['Scientist'].append(author_obj)
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
                            authorship_obj, created = self.create_update_authorship(author_obj, index, total_authors,
                                                                                    article_obj)
                            if created:
                                created_objs['Authorship'].append(authorship_obj)
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
                                        created_objs['Institution'].append(institution_obj)
                                    ###
                                    # 7) Create/Retrieve author's affiliation
                                    ###
                                    affiliation_obj, created = Affiliation.objects.get_or_create(
                                        scientist=author_obj,
                                        institution=institution_obj
                                    )
                                    if created:
                                        created_objs['Institution'].append(affiliation_obj)
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
                    return article_obj, created_objs
            except (IntegrityError, KeyError) as e:
                # Transaction failed, log the error and continue with the paper
                logging.error(e)
                return None, None

