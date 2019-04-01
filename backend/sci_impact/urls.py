from django.conf.urls import include
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views


urlpatterns = [
    path('scientists/', views.ScientistList.as_view(), name='snippet-list'),
    path('scientists/<int:pk>/', views.ScientistDetail.as_view()),
    path('api-auth/', include('rest_framework.urls')),
]

urlpatterns = format_suffix_patterns(urlpatterns)
