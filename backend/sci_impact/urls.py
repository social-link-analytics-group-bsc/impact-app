from django.urls import path, include
#from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.routers import DefaultRouter
from sci_impact import views


# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('scientists', views.ScientistViewSet)


urlpatterns = [
    # ex: /api/scientist/
    #re_path(r'^scientists/$', scientist_list),
    # ex: /api/scientist/1
    #re_path(r'^scientists/(?P<pk>[0-9]+)/$', scientist_detail),
    path('', include(router.urls)),
]

#urlpatterns = format_suffix_patterns(urlpatterns)
