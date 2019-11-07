from django.db.models import Count, Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework import viewsets
from sci_impact.models import Scientist, Article, ArtifactCitation, Impact, ImpactDetail, FieldCitations, Artifact, \
                              Authorship, Institution
from sci_impact.api.serializers import ScientistSerializer, ArticleSerializer


start_year = 2009
end_year = 2016
years_range = list(range(start_year, end_year + 1))


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
        articles = Article.objects.filter(year__in=years_range, inb_pi_as_author=True, created_by=request.user)
        total_citations = Article.objects.filter(year__in=range(2009,2017), inb_pi_as_author=True).\
                                                 aggregate(Sum('cited_by'))['cited_by__sum']
        total_pis = Scientist.objects.filter(is_pi_inb=True).count()
        response = {
            'total_year_range': (years_range[0], years_range[-1]),
            'total_pis': total_pis,
            'total_articles': articles.count(),
            'articles_source': 'PubMed and Scopus',
            'total_citations': total_citations,
            'citations_source': 'PubMed Central and Scopus',
            'total_projects': 26,
            'projects_source': 'Cordis',
        }
        return Response(response)


class ArticlesByYear(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        articles = Article.objects.filter(year__in=years_range, inb_pi_as_author=True, created_by=request.user)
        article_by_year_objs = articles.values('year').annotate(count=Count('year')).order_by('year')
        articles_by_year = [dict['count'] for dict in article_by_year_objs]
        response = {
            'years': years_range,
            'articles_by_year': articles_by_year,
        }
        return Response(response)


class CitationsByYear(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        citations_by_year = Article.objects.filter(year__in=range(2009,2017), inb_pi_as_author=True,
                                                   created_by=request.user).values('year').\
                                                   annotate(citations=Sum('cited_by')).order_by('year')
        citations = [citation_by_year['citations'] for citation_by_year in citations_by_year]
        response = {
            'years': years_range,
            'citations_by_year': citations
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


def get_impact_query(impact_obj, user):
    impact_type, impact_obj_id = impact_obj.split('_')
    impact_query = {'created_by': user}
    if impact_type == 'institution':
        impact_obj_name = Institution.objects.get(is_inb=True).name
        impact_query['institution_id'] = impact_obj_id
    else:
        scientist_obj = Scientist.objects.get(id=impact_obj_id)
        impact_obj_name = scientist_obj.first_name + ' ' + scientist_obj.last_name
        impact_query['scientist_id'] = impact_obj_id
    return impact_query, impact_obj_name


class SciImpactTotal(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None, **kwargs):
        impact_query, impact_obj_name = get_impact_query(kwargs.get('impact_obj'), request.user)
        sci_impact_obj = Impact.objects.select_related().filter(**impact_query).latest('created')
        sci_impact_year_range = (sci_impact_obj.start_year, sci_impact_obj.end_year)
        sci_impact = round(sci_impact_obj.total_weighted_impact, 2)
        sci_impact_details = ImpactDetail.objects.select_related().\
            filter(impact_header=sci_impact_obj, created_by=request.user)
        total_articles = sci_impact_details.aggregate(Sum('publications'))['publications__sum']
        total_citations = sci_impact_details.aggregate(Sum('citations'))['citations__sum']
        citations_per_publications = round(total_citations / total_articles, 2)
        response = {
            'articles_source': 'PubMed and Scopus',
            'citations_source': 'PubMed Central and Scopus',
            'sci_impact_year_range': sci_impact_year_range,
            'sci_impact_total_articles': total_articles,
            'sci_impact_total_citations': total_citations,
            'sci_impact_citations_per_publications': citations_per_publications,
            'sci_impact_score': sci_impact,
            'impact_obj_name': impact_obj_name
        }
        return Response(response)


class SciImpactTable(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None, **kwargs):
        impact_query, _ = get_impact_query(kwargs.get('impact_obj'), request.user)
        sci_impact_obj = Impact.objects.select_related().filter(**impact_query).latest('created')
        sci_impact_details = ImpactDetail.objects.select_related().filter(impact_header=sci_impact_obj,
                                                                          created_by=request.user)
        years_range = []
        table_rows, field_cpp_years = [], []
        total_citations = 0
        for sci_impact_detail in sci_impact_details:
            years_range.append(sci_impact_detail.year)
            fc = FieldCitations.objects.select_related().get(year=sci_impact_detail.year)
            field_cpp_years.append(round(fc.avg_citations_field, 2))
            total_citations += sci_impact_detail.citations
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
        table_foot = {
            'total_publications': sci_impact_obj.total_publications,
            'total_citations': total_citations,
            'total_impact': round(sci_impact_obj.total_weighted_impact,2)
        }
        response = {'body': table_rows, 'foot': table_foot}
        return Response(response)


class AvgCitationsByYear(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None, **kwargs):
        impact_query, _ = get_impact_query(kwargs.get('impact_obj'), request.user)
        sci_impact_obj = Impact.objects.select_related().filter(**impact_query).latest('created')
        years = list(range(sci_impact_obj.start_year, sci_impact_obj.end_year + 1))
        field_cpp, cpp = [], []
        for year in years:
            si = ImpactDetail.objects.select_related().filter(impact_header=sci_impact_obj, year=year,
                                                              created_by=request.user).latest('created')
            cpp.append(round(si.avg_citations_per_publication, 2))
            fc = FieldCitations.objects.select_related().get(year=year)
            field_cpp.append(round(fc.avg_citations_field, 2))
        response = {
            'years': years,
            'datasets': [cpp, field_cpp]
        }
        if kwargs.get('impact_obj').split('_')[0] == 'scientist':
            inb_impact_obj = Impact.objects.filter(institution=Institution.objects.get(is_inb=True)).latest('created')
            inb_impact_details = ImpactDetail.objects.filter(impact_header=inb_impact_obj, created_by=request.user).\
                values('year', 'avg_citations_per_publication').order_by('year').values('avg_citations_per_publication')
            inb_cpp = [round(dict['avg_citations_per_publication'], 2) for dict in inb_impact_details]
            response['datasets'].append(inb_cpp)
        return Response(response)


def prepare_pi_impact_data(pi_obj, current_user):
    sci_impact_obj = Impact.objects.select_related().filter(scientist=pi_obj, created_by=current_user).latest('created')
    sci_impact_details = ImpactDetail.objects.select_related().filter(impact_header=sci_impact_obj,
                                                                      created_by=current_user)
    cpp_years = [{'year': sci_impact_detail.year, 'cpp': round(sci_impact_detail.avg_citations_per_publication, 2)}
                 for sci_impact_detail in sci_impact_details]
    cpp_years = sorted(cpp_years, key=lambda k: k['year'])
    pi_impact_data = {
        'citations_per_publications_year': cpp_years
    }
    return pi_impact_data


class AvgCitationsByYearPIs(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        pis_obj = Scientist.objects.select_related().filter(is_pi_inb=True, created_by=request.user)
        datasets, dataset_names, years = [], [], []
        for pi_obj in pis_obj:
            dataset_names.append(str(pi_obj))
            pi_impact_data = prepare_pi_impact_data(pi_obj, request.user)
            datasets.append([dict['cpp'] for dict in pi_impact_data['citations_per_publications_year']])
            if not years:
                years = [dict['year'] for dict in pi_impact_data['citations_per_publications_year']]
        field_cpp_years = []
        for year in years:
            fc = FieldCitations.objects.select_related().get(year=year, created_by=request.user)
            field_cpp_years.append(round(fc.avg_citations_field, 2))
        datasets.append(field_cpp_years)
        dataset_names.append('the field')
        response = {
            'years': years,
            'dataset_names': dataset_names,
            'datasets': datasets
        }
        return Response(response)


class ArticlesPI(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None, **kwargs):
        impact_query, _ = get_impact_query(kwargs.get('impact_obj'), request.user)
        sci_impact_obj = Impact.objects.select_related().filter(**impact_query).latest('created')
        years_range = list(range(sci_impact_obj.start_year, sci_impact_obj.end_year+1))
        pi_artifacts = Artifact.objects.filter(pk__in=Authorship.objects.filter(author=sci_impact_obj.scientist,
                                                                               created_by=request.user).
                                              distinct('artifact').values('artifact'), year__in=years_range,
                                              created_by=request.user)
        table_rows = []
        for artifact in pi_artifacts:
            table_rows.append(
                {
                    'year': artifact.year,
                    'title': artifact.title,
                    'citations': artifact.article.cited_by
                }
            )
        response = {'body': table_rows}
        return Response(response)