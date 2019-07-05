from django.urls import path

from dashboard.views import index, sci_impact, sci_impact_methodology


urlpatterns = [
    path('sci_impact/', sci_impact, name='sci_impact'),  # dashboard scientific impact
    path('sci_impact/methodology/', sci_impact_methodology, name='sci_impact_methodology'),
    path('sci_impact/<str:pi>/', sci_impact, name='sci_impact'),  # dashboard scientific impact
    path('', index, name='dashboard'),  # dashboard
]
