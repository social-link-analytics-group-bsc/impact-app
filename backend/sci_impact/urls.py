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
    path('total-data/', views.TotalData.as_view()),
    path('articles-by-year/', views.ArticlesByYear.as_view()),
    path('citations-by-year/', views.CitationsByYear.as_view()),
    path('sci-impact-total-data/', views.SciImpactTotal.as_view()),
    re_path(r'sci-impact-total-data/[a-z]+/', views.SciImpactTotal.as_view()),
    path('sci-impact-table/', views.SciImpactTable.as_view()),
    re_path(r'sci-impact-table/[a-z]+/', views.SciImpactTable.as_view())
]

#urlpatterns = format_suffix_patterns(urlpatterns)
