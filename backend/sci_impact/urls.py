from django.conf.urls import include
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework_swagger.views import get_swagger_view
from . import views

schema_view = get_swagger_view(title='Scientific Impact API')

urlpatterns = [
    path('', schema_view),
    path('scientists/', views.ScientistList.as_view()),
    path('scientists/<int:pk>/', views.ScientistDetail.as_view()),
    path('api-auth/', include('rest_framework.urls')),
]

urlpatterns = format_suffix_patterns(urlpatterns)
