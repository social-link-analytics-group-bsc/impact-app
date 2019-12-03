from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from social_impact.api import views


# Create a router and register our viewsets with it.
router = DefaultRouter()


urlpatterns = [
    path('', include(router.urls)),
    path('projects-meta-data/', views.ProjectsMetaData.as_view()),
    path('projects/', views.ProjectList.as_view()),
    path('projects/impact/<str:id>/overall/', views.ProjectImpactOverall.as_view()),
    path('projects/impact/<str:id>/details/', views.ProjectImpactDetails.as_view()),
]

