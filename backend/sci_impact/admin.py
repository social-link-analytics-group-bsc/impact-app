from collections import defaultdict
from data_collector.pubmed import EntrezClient
from django.contrib import admin, messages
from sci_impact.models import Scientist, Country, Institution, City, Region, Affiliation, Venue, CustomField, Article

import logging
import pathlib

logging.basicConfig(filename=str(pathlib.Path(__file__).parents[1].joinpath('impact_app.log')),
                    level=logging.DEBUG)


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

    def get_articles(self, request, queryset):
        ec = EntrezClient()
        for obj in queryset:
            scientist_obj = obj
            scientist_name = scientist_obj.first_name + ' ' + scientist_obj.last_name
            logging.info(f"Getting articles of {scientist_name}")
            results = ec.search(f"{scientist_name}[author]")
            papers = ec.fetch_in_batch_from_history(results['Count'], results['WebEnv'], results['QueryKey'])
            for i, paper in enumerate(papers):
                paper_info = paper['MedlineCitation']['Article']
                logging.info(f"Found the paper: {paper_info['ArticleTitle']}")
                pubmed_id_obj = CustomField.objects.create(name='PubMed Id', value=paper['MedlineCitation']['PMID'],
                                                           type='str', source='')
                self.objs_created['CustomField'].append(pubmed_id_obj)
                venue_dict = {
                    'name': '',
                    'volume': '',
                    'number': '',
                    'issue': '',
                    'publisher': ''
                }
                venue_obj, created = Venue.objects.get_or_create(venue_dict)
                if created: self.objs_created['Venue'].append(venue_obj)
                article_dict = {
                    'title': paper_info['ArticleTitle'],
                    'year': paper_info[''],
                    'url': paper_info[''],
                    'language': paper_info[''],
                    'doi': paper_info[''],
                    'pages': paper_info[''],
                    'category': paper_info[''],
                    'academic_db': 'pubmed',
                    'venue': venue_obj,
                }
                article_obj, created = Article.objects.get_or_create(article_dict, defaults={'doi': ''})
                if created: article_obj.add(pubmed_id_obj)
                self.objs_created['Article'].append(article_obj)
    get_articles.short_description = 'Get scientist\'s articles (PubMed)'


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'city', 'web_page')


@admin.register(Affiliation)
class AffiliationAdmin(admin.ModelAdmin):
    list_display = ('scientist', 'institution', 'joined_date')
