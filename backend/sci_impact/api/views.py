import datetime

from collections import defaultdict
from django.db.models import Count, Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework import viewsets
from sci_impact.models import Scientist, Article, ArtifactCitation, Impact, ImpactDetail, FieldCitations
from sci_impact.api.serializers import ScientistSerializer, ArticleSerializer


class ScientistViewSet(viewsets.ModelViewSet):
    """
    retrieve:
    Return the given scientist.

    list:
    Return a list of all the existing scientists.

    create:
    Create a new scientist instance.

    delete:
    Delete the given scientist.
    """
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Scientist.objects.all()
    serializer_class = ScientistSerializer
    http_method_names = ['get', 'post', 'head', 'delete']


class ArticleViewSet(viewsets.ModelViewSet):
    """
    retrieve:
    Return the given scientific publication.

    list:
    Return a list of all the existing scientific publication.

    create:
    Create a new scientific publication.

    delete:
    Delete the given scientific publication.
    """
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    http_method_names = ['get', 'post', 'head', 'delete']


class TotalData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        year_range = (2003, datetime.datetime.now().year-1)
        articles = Article.objects.filter(year__gte=year_range[0]).filter(year__lte=year_range[1]). \
                         filter(inb_pi_as_author=True)
        total_citations = ArtifactCitation.objects.select_related().filter(to_artifact__in=articles).count()
        total_pis = Scientist.objects.filter(is_pi_inb=True).count()
        response = {
            'total_year_range': year_range,
            'total_pis': total_pis,
            'total_articles': articles.count(),
            'articles_source': 'PubMed',
            'total_citations': total_citations,
            'citations_source': 'PubMed Central',
            'total_projects': 26,
            'projects_source': 'Cordis',
        }
        return Response(response)


class ArticlesByYear(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        year_range = (2003, datetime.datetime.now().year - 1)
        articles = Article.objects.filter(year__gte=year_range[0]).filter(year__lte=year_range[1]). \
            filter(inb_pi_as_author=True)
        article_by_year_objs = articles.values('year').annotate(count=Count('year')).order_by('year')
        years = [dict['year'] for dict in article_by_year_objs]
        articles_by_year = [dict['count'] for dict in article_by_year_objs]
        chart = {
            'labels': years,
            'datasets': [
                {
                    'data': articles_by_year,
                    'label': 'Articles',
                    'color': '#4285F4',
                    'fill': False
                }
            ]
        }
        response = {
            'years': years,
            'articles_by_year': articles_by_year,
            'chart': chart
        }
        return Response(response)


class CitationsByYear(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        year_range = (2003, datetime.datetime.now().year - 1)
        articles = Article.objects.filter(year__gte=year_range[0]).filter(year__lte=year_range[1]). \
            filter(inb_pi_as_author=True)
        citations = ArtifactCitation.objects.select_related().filter(to_artifact__in=articles)
        citations_by_year_dict = defaultdict(int)
        for citation in citations:
            if citation.from_artifact.year <= year_range[1]:
                citations_by_year_dict[citation.from_artifact.year] += 1
        years = sorted(citations_by_year_dict.keys())
        citations_by_year = [citations_by_year_dict[year] for year in sorted(citations_by_year_dict.keys())]
        chart = {
            'labels': years,
            'datasets': [
                {
                    'data': citations_by_year,
                    'label': 'Citations',
                    'color': '#17a2b8',
                    'fill': False
                }
            ],
        }
        response = {
            'years': years,
            'citations_by_year': citations_by_year,
            'chart': chart
        }
        return Response(response)


def get_impact_obj_name(impact_obj):
    mapping_dict = {
        'carazo': 'Jose M Carazo',
        'dopazo': 'Joaquin Dopazo',
        'gelpi': 'Jose L Gelpi',
        'guigo': 'Roderic Guigo',
        'gut': 'Ivo G Gut',
        'navarro': 'Arcadi Navarro',
        'orozco': 'Modesto Orozco',
        'sanz': 'Ferran Sanz',
        'trellez': 'Oswaldo R Trellez',
        'valencia': 'Alfonso Valencia'
    }
    if impact_obj:
        return mapping_dict[impact_obj]
    else:
        return 'INB'


class SciImpactTotal(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        impact_obj = request.GET.get('impact_obj')
        impact_name = f"Scientific Impact {get_impact_obj_name(impact_obj)} 2009-2016"
        sci_impact_obj = Impact.objects.select_related().get(name=impact_name)
        sci_impact_year_range = (sci_impact_obj.start_year, sci_impact_obj.end_year)
        sci_impact = round(sci_impact_obj.total_weighted_impact, 2)
        sci_impact_details = ImpactDetail.objects.select_related().filter(impact_header=sci_impact_obj)
        total_articles = sci_impact_details.aggregate(Sum('publications'))['publications__sum']
        total_citations = sci_impact_details.aggregate(Sum('citations'))['citations__sum']
        citations_per_publications = round(total_citations / total_articles, 2)
        response = {
            'articles_source': 'PubMed',
            'citations_source': 'PubMed Central',
            'sci_impact_year_range': sci_impact_year_range,
            'sci_impact_total_articles': total_articles,
            'sci_impact_total_citations': total_citations,
            'sci_impact_citations_per_publications': citations_per_publications,
            'sci_impact_score': sci_impact
        }
        return Response(response)


class SciImpactTable(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        impact_obj = request.GET.get('impact_obj')
        impact_name = f"Scientific Impact {get_impact_obj_name(impact_obj)} 2009-2016"
        sci_impact_obj = Impact.objects.select_related().get(name=impact_name)
        sci_impact_details = ImpactDetail.objects.select_related().filter(impact_header=sci_impact_obj)
        years_range = []
        table_headers = ['Year', 'Publications', 'Citations', 'Citations per Publications', '% Not Cited Publications',
                         '% Self-citations', 'Avg. Citations in the Field', 'Scientific Impact',
                         '% Publication of the Total', 'Weighted Impact']
        table_rows, field_cpp_years = [], []
        for sci_impact_detail in sci_impact_details:
            years_range.append(sci_impact_detail.year)
            fc = FieldCitations.objects.select_related().get(year=sci_impact_detail.year)
            field_cpp_years.append(round(fc.avg_citations_field, 2))
            table_rows.append(
                {
                    'year': sci_impact_detail.year,
                    'publications': sci_impact_detail.publications,
                    'citations': sci_impact_detail.citations,
                    'citations_per_publications': round(sci_impact_detail.avg_citations_per_publication, 2),
                    'prop_not_cited_publications': round(sci_impact_detail.prop_not_cited_publications, 2),
                    'prop_self_citations': round(sci_impact_detail.prop_self_citations, 2),
                    'avg_field_citations': round(fc.avg_citations_field, 2),
                    'impact_field': round(sci_impact_detail.impact_field, 2),
                    'prop_publications_year': round(sci_impact_detail.prop_publications_year, 2),
                    'weighted_impact_field': round(sci_impact_detail.weighted_impact_field, 2)
                }
            )
        response = {'header': table_headers, 'body': table_rows}
        return Response(response)