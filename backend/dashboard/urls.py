from django.urls import path

from dashboard.views import dashboard_idx, dashboard_sci_impact, dashboard_sci_impact_methodology


urlpatterns = [
    path('sci_impact/', dashboard_sci_impact, name='sci_impact'),  # dashboard scientific impact
    path('sci_impact/<str:pi>/', dashboard_sci_impact, name='sci_impact'),  # dashboard scientific impact
    path('sci_impact/methodology/', dashboard_sci_impact_methodology, name='sci_impact_methodology'),
    path('', dashboard_idx, name='dashboard'),  # dashboard
]
