from django.urls import path, include, re_path
#from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.routers import DefaultRouter
from sci_impact.api import views


# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('scientists', views.ScientistViewSet)
router.register('articles', views.ArticleViewSet)


urlpatterns = [
    # ex: /api/scientist/
    #re_path(r'^scientists/$', scientist_list),
    # ex: /api/scientist/1
    #re_path(r'^scientists/(?P<pk>[0-9]+)/$', scientist_detail),
    path('', include(router.urls)),
    path('articles-by-year/', views.ArticlesByYear.as_view()),
    path('citations-by-year/', views.CitationsByYear.as_view()),
    path('sci-impact-total-data/', views.SciImpactTotal.as_view()),
    path('sci-impact-total-data/<str:impact_obj>/', views.SciImpactTotal.as_view()),
    path('sci-impact-table/', views.SciImpactTable.as_view()),
    path('sci-impact-table/<str:impact_obj>/', views.SciImpactTable.as_view()),
    path('avg-citations-by-year/', views.AvgCitationsByYear.as_view()),
    path('avg-citations-by-year/<str:impact_obj>/', views.AvgCitationsByYear.as_view()),
    path('avg-citations-by-year-pis/', views.AvgCitationsByYearPIs.as_view()),
    path('articles-table/', views.ArticlesPI.as_view()),
    path('articles-table/<str:impact_obj>/', views.ArticlesPI.as_view()),
]

#urlpatterns = format_suffix_patterns(urlpatterns)
