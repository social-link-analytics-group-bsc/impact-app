from django import forms
from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path
from sci_impact.models import Country, Institution
from social_impact.models import Project, Publication, SocialImpactSearch, SocialImpactSearchPublication, \
                                 ImpactMention, SIORMeasurement
from social_impact.tasks import search_social_impact_mentions
from shutil import copyfile

import csv
import datetime
import logging
import re
import pathlib
import os


logger = logging.getLogger(__name__)


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


class ExportCsvMixin:
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response
    export_as_csv.short_description = 'Export Selected'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = ('name', 'description', 'twitter_account', 'status', 'start_date',
                    'end_date', 'funded_by', 'overall_budget', 'budget_eu',
                    'pretty_coordinator', 'pretty_coordinator_country', 'cordis_url')
    change_list_template = 'admin/project_changelist.html'
    list_filter = ('status',)
    ordering = ('name', 'status', 'start_date', 'end_date', 'overall_budget')
    search_fields = ('name',)

    def pretty_coordinator(self, obj):
        return obj.coordinator
    pretty_coordinator.short_description = 'Coordinator'

    def pretty_coordinator_country(self, obj):
        return obj.coordinator_country
    pretty_coordinator_country.short_description = 'Country of Coordinator'

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def __process_quantity(self, quantity):
        # remove extra spaces
        quantity = ''.join(quantity.split())
        # remove currency symbol
        quantity = re.sub(r'[^0-9,]+', '', quantity)
        # replace comma with point if exists
        quantity = re.sub(r'[,]', '.', quantity)
        # convert to float
        quantity = float(quantity)
        return quantity

    def __get_country(self, country_str):
        if country_str:
            try:
                country_obj = Country.objects.get(name__iexact=country_str)
            except Country.DoesNotExist as e:
                country_obj = Country.objects.filter(alternative_names__icontains=country_str)[0]
            return country_obj
        else:
            return None

    def __get_institution(self, institution_str, country_obj, user):
        query = {'name__iexact': institution_str}
        if country_obj:
            query['country'] = country_obj
        if institution_str:
            try:
                institution_obj = Institution.objects.get(**query)
            except Institution.DoesNotExist as e:
                institution_obj = Institution(name=institution_str, country=country_obj, created_by=user)
                institution_obj.save()
                logger.info(f"Institution: {institution_obj.name} created!")
            return institution_obj
        else:
            return None

    def __process_csv(self, csv_reader, user):
        obj_names = {'created': [], 'updated': []}
        for row in csv_reader:
            coordinator_country = self.__get_country(row['Country'])
            coordinator = self.__get_institution(row['Coordinated by'].title().strip(), coordinator_country, user)
            project_dict = {
                'name': row['Acronymous'].strip(),
                'description': row['European Projects'],
                'start_date': datetime.datetime.strptime(row['Start'],'%d.%m.%Y'),
                'end_date': datetime.datetime.strptime(row['End'], '%d.%m.%Y'),
                'funded_by': row['Funded under'].strip(),
                'coordinator': coordinator,
                'coordination_country': coordinator_country,
                'cordis_url': row['CORDIS'],
                'created_by': user
            }
            if row['Twitter Handler']:
                project_dict['twitter_account'] = row['Twitter Handler'].replace('@', '').strip()  # remove @
            if row['Status'].lower().strip() == 'active':
                project_dict['status'] = 'active'
            elif row['Status'].lower().strip() == 'finished':
                project_dict['status'] = 'finished'
            else:
                project_dict['status'] = 'other'
            if row['Twitter Hashtag']:
                project_dict['twitter_hashtag'] = row['Twitter Handler'].replace('#', '').strip()  # remove #
            if row['Overall budget']:
                project_dict['overall_budget'] = self.__process_quantity(row['Overall budget'])
            if row['EU contribution']:
                project_dict['budget_eu'] = self.__process_quantity(row['EU contribution'])
            obj, created = Project.objects.update_or_create(
                name=project_dict['name'],
                defaults=project_dict,
            )
            if created:
                obj_names['created'].append(obj.name)
                logger.info(f"Project {obj.name} created!")
            else:
                obj_names['updated'].append(obj.name)
                logger.info(f"Project {obj.name} updated!")
        return obj_names

    def __decode_utf8(self, input_iter):
        for l in input_iter:
            yield l.decode('utf-8')

    def __create_import_output_message(self, obj_names):
        msg = ''
        if len(obj_names['created']) > 0:
            msg = 'Project created:\n'
            for obj_name in obj_names['created']:
                msg += '-' + obj_name + '\n'
        if len(obj_names['updated']) > 0:
            msg = 'Project updated:\n'
            for obj_name in obj_names['updated']:
                msg += '-' + obj_name + '\n'
        return msg

    def import_csv(self, request):
        if request.method == 'POST':
            csv_file = request.FILES['csv_file']
            csv_reader = csv.DictReader(self.__decode_utf8(csv_file))
            # Create Project objects from passed in data
            obj_names = self.__process_csv(csv_reader, request.user)
            output_msg = self.__create_import_output_message(obj_names)
            self.message_user(request, 'The following objects were created/updated from the '
                                       'imported csv file'+'\n'+output_msg, level=messages.SUCCESS)
            return redirect('..')
        form = CsvImportForm()
        payload = {'form': form}
        return render(
            request, 'admin/csv_form.html', payload
        )


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('project', 'name', 'file')
    search_fields = ('project__name', 'name')
    change_list_template = 'admin/publication_changelist.html'

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('bulk-import-publications/', self.bulk_load_publications),
        ]
        return my_urls + urls

    def bulk_load_publications(self, request):
        origin_dir = './social_impact/tmp'
        doc_dir = './media/docs'
        file_extension = 'pdf'
        inb_user = User.objects.get(username='inb')
        for root_name, dir_names, file_names in os.walk(origin_dir):
            for file_name in file_names:
                logger.info(f"Analyzing file: {file_name}")
                # check if file_name is a pdf
                if file_name.endswith(file_extension):
                    # found a pdf
                    file_path = pathlib.Path(root_name, file_name)
                    # search project
                    parent_dir = str(file_path.parent).split('/')[-1]
                    try:
                        project_obj = Project.objects.get(name__iexact=parent_dir)
                        # copy file
                        file_dir = str(pathlib.Path(doc_dir, project_obj.name + '__' + file_name))
                        copyfile(str(file_path), file_dir)
                        # set new dir
                        publication_dict = {
                            'name': file_name,
                            'project': project_obj,
                            'file':  file_dir,
                            'created_by': inb_user
                        }
                        obj, created = Publication.objects.update_or_create(
                            file=file_dir,
                            defaults=publication_dict,
                        )
                        if created:
                            logger.info(f"Publication {file_dir} created!")
                    except Project.DoesNotExist as e:
                        logger.info(f"Project {parent_dir} does not exists!")
        return redirect('..')


@admin.register(SocialImpactSearch)
class SocialImpactSearchAdmin(admin.ModelAdmin):
    list_display = ('name', 'dictionary', 'completed')
    actions = ['execute_search']

    def execute_search(self, request, queryset):
        searches = []
        payload = {'search_ids': [], 'current_user': request.user}
        for search in queryset:
            payload['search_ids'].append(search.id)
        search_social_impact_mentions.delay(searches)
        msg = f"The process of searching mentions of social impact has started. Depending on the number of publications " \
              f"to be queried, it might take a while to complete. Please refer to the log to get updates " \
              f"on the progress of the process."
        self.message_user(request, msg, level=messages.SUCCESS)
    execute_search.short_description = 'Execute Search'

    def save_model(self, request, obj, form, change):
        super(SocialImpactSearchAdmin, self).save_model(request, obj, form, change)
        if change:
            # remove all objects associated to this object
            SocialImpactSearchPublication.objects.filter(social_impact_header=obj.id).delete()
        publications = form.cleaned_data.get('publications')
        for publication in publications:
            record_dict = {
                'social_impact_header': obj,
                'publication': publication,
                'created_by': request.user
            }
            sisp_obj = SocialImpactSearchPublication(**record_dict)
            sisp_obj.save()

    def delete_queryset(self, request, queryset):
        for search in queryset:
            SocialImpactSearchPublication.objects.filter(social_impact_header=search.id).delete()
        queryset.delete()


@admin.register(SocialImpactSearchPublication)
class SocialImpactSearchPublicationAdmin(admin.ModelAdmin):
    list_display = ('social_impact_header', 'publication', 'completed')
    actions = ['mark_search_as_completed']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def mark_search_as_completed(self, request, queryset):
        for search_publication in queryset:
            search_publication.completed = True
            search_publication.save()
    mark_search_as_completed.short_description = 'Mark search as completed'


@admin.register(ImpactMention)
class ImpactMentionAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = ('search', 'publication', 'page', 'sentence', 'impact_mention', 'mention_is_correct')
    change_list_template = 'admin/impact_mention_changelist.html'

    def has_add_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def __decode_utf8(self, input_iter):
        for l in input_iter:
            yield l.decode('utf-8')

    def __process_csv(self, csv_reader, user):
        for row in csv_reader:
            publication = Publication.objects.get(project_id=row['project_id'], name=row['file'])
            mention_dict = {
                'publication': publication,
                'page': row['page'],
                'sentence': row['sentence'],
                'impact_mention': row['impact mention'],
                'created_by': user
            }
            impact_mention_obj = ImpactMention(**mention_dict)
            impact_mention_obj.save()

    def import_csv(self, request):
        if request.method == 'POST':
            csv_file = request.FILES['csv_file']
            csv_reader = csv.DictReader(self.__decode_utf8(csv_file))
            # Create Project objects from passed in data
            self.__process_csv(csv_reader, request.user)
            self.message_user(request, 'The process has successfully finished!', level=messages.SUCCESS)
            return redirect('..')
        form = CsvImportForm()
        payload = {'form': form}
        return render(
            request, 'admin/csv_form.html', payload
        )


class CustomSIORModelForm(forms.ModelForm):
    class Meta:
        model = SIORMeasurement
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CustomSIORModelForm, self).__init__(*args, **kwargs)
        impact_mentions = ImpactMention.objects.filter(mention_is_correct=True)
        self.fields['evidence'].queryset = impact_mentions
        project_ids = []
        for impact_mention in impact_mentions:
            project_ids.append(impact_mention.publication.project.id)
        self.fields['project'].queryset = Project.objects.filter(pk__in=project_ids)


@admin.register(SIORMeasurement)
class SIORMeasurementAdmin(admin.ModelAdmin):
    list_display = ('project', 'pretty_evidence', 'scientific_evidence', 'sdg', 'percentage_improvement',
                    'description_achievement', 'sustainability', 'description_sustainability', 'replicability',
                    'description_replicability', 'score')
    form = CustomSIORModelForm

    def pretty_evidence(self, obj):
        return obj.evidence
    pretty_evidence.short_description = 'Evidence'

    def save_model(self, request, obj, form, change):
        super(SIORMeasurementAdmin, self).save_model(request, obj, form, change)
        if obj.sustainability and obj.replicability and obj.scientific_evidence:
            if obj.percentage_improvement >= 30:
                obj.score = 7
            elif obj.percentage_improvement >= 20:
                obj.score = 6
            elif obj.percentage_improvement >= 10:
                obj.score = 5
            else:
                obj.score = 4
        else:
            if (obj.sustainability and obj.replicability) or \
               (obj.sustainability and obj.scientific_evidence) or \
               (obj.replicability and obj.scientific_evidence):
                obj.score = 3
            else:
                if obj.sustainability or obj.replicability or obj.scientific_evidence:
                    obj.score = 2
                else:
                    obj.score = 1
        obj.save()
