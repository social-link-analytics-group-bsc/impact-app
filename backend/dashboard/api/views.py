from django.db.models import Sum
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from sci_impact.models import Scientist, Article
from social_impact.models import Project


start_year = 2009
end_year = 2016
years_range = list(range(start_year, end_year + 1))


class TotalData(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        articles = Article.objects.filter(year__in=years_range, inb_pi_as_author=True, created_by=request.user)
        total_citations = Article.objects.filter(year__in=years_range, inb_pi_as_author=True). \
            aggregate(Sum('cited_by'))['cited_by__sum']
        total_pis = Scientist.objects.filter(is_pi_inb=True).count()
        total_projects = Project.objects.all().count()
        response = {
            'total_year_range': (years_range[0], years_range[-1]),
            'total_pis': total_pis,
            'total_articles': articles.count(),
            'articles_source': 'PubMed and Scopus',
            'total_citations': total_citations,
            'citations_source': 'PubMed Central and Scopus',
            'total_projects': total_projects,
            'projects_source': 'Cordis',
        }
        return Response(response)