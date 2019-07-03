from rest_framework import serializers
from sci_impact.models import Scientist, Institution, Article


class ScientistSerializer(serializers.ModelSerializer):
    nationality = serializers.SlugRelatedField(many=False, read_only=True, slug_field='name')

    class Meta:
        model = Scientist
        fields = [
            'id',
            'first_name',
            'last_name',
            'nationality',
            'birth_date',
            'gender',
            'articles',
            'articles_as_first_author',
            'articles_as_last_author',
            'articles_with_citations',
            'books',
            'patents',
            'datasets',
            'tools',
            'article_citations',
            'tool_citations',
            'total_citations',
            'h_index',
            'i10_index',
        ]
        read_only_fields = [
            'id'
        ]


class ArticleSerializer(serializers.ModelSerializer):
    venue = serializers.SlugRelatedField(many=False, read_only=True, slug_field='name')

    class Meta:
        model = Article
        fields = [
            'title',
            'url',
            'year',
            'doi',
            'pages',
            'keywords',
            'venue',
            'academic_db'
        ]
