from django.contrib import admin
from sci_impact.models import Scientist, Country, Institution, City, Region


class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'iso_code')


class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')


class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'country', 'wikipage')


class ScientistAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'gender')


class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'city', 'web_page')


admin.site.register(Country, CountryAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(Scientist, ScientistAdmin)
admin.site.register(Institution, InstitutionAdmin)

