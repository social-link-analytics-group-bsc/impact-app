from rest_framework import serializers
from sci_impact.models import Country, City, Region, Citation,Scientist, Book, Dataset, Tool, \
                              Patent, Institution, Affiliation


class ScientistSerializer(serializers.ModelSerializer):

    class Meta:
        model = Scientist




