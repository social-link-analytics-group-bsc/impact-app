from django.urls import path

from dashboard.views import index, sci_impact, sci_impact_methodology, social_impact, social_impact_project, \
    social_impact_methodology
from dashboard.api import views


urlpatterns = [
    path('social_impact/projects/impact/<str:id>/', social_impact_project, name='social_impact_project'),  # project social impact
    path('social_impact/projects/', social_impact, name='social_impact_projects'),  # projects
    path('social_impact/methodology/', social_impact_methodology, name='social_impact_methodology'),
    path('sci_impact/', sci_impact, name='sci_impact'),  # dashboard scientific impact
    path('sci_impact/methodology/', sci_impact_methodology, name='sci_impact_methodology'),
    path('sci_impact/<str:id>/', sci_impact, name='sci_impact'),  # dashboard scientific impact
    path('total-data/', views.TotalData.as_view()),
    path('', index, name='dashboard'),  # dashboard
]
