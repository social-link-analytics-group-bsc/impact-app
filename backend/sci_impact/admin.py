from django.contrib import admin
from sci_impact.models import Scientist, Country, Institution, City, Region


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


class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')


class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'country', 'wikipage')


class ScientistAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'gender')
    ordering = ('last_name', )
    search_fields = ('first_name', 'last_name',)


class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'city', 'web_page')


admin.site.register(Country, CountryAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(Scientist, ScientistAdmin)
admin.site.register(Institution, InstitutionAdmin)

