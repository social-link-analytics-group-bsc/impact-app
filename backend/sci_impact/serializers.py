from rest_framework import serializers
from sci_impact.models import Country, City, Region, Citation,Scientist, Book, Dataset, Tool, \
                              Patent, Institution, Affiliation


class ScientistSerializer(serializers.ModelSerializer):
    country = serializers.SlugRelatedField(many=False, read_only=True, slug_field='name')

    class Meta:
        model = Scientist
        fields = '__all__'
