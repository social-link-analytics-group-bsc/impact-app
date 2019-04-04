from django.contrib import admin
from sci_impact.models import Scientist, Country, Institution, City, Region, Affiliation


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'iso_code')
    #actions = ['load_countries']
    ordering = ('name',)
    search_fields = ('name',)

    def load_countries(self, request, queryset):
        with open(str('sci_impact/data/country_list.txt'), 'r') as f:
            for _, line in enumerate(f):
                line = line.split(':')
                country_name = line[1].replace('\n', '')
                country_code = line[0].replace('\n', '')
                Country.objects.create(name=country_name, iso_code=country_code)
        Country.objects.create(name='USA')
        Country.objects.create(name='UK')
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


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'city', 'web_page')


@admin.register(Affiliation)
class AffiliationAdmin(admin.ModelAdmin):
    list_display = ('scientist', 'institution', 'joined_date')
