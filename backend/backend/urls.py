"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib.auth.models import User, Group
from django.contrib import admin
from django.urls import re_path
from django.conf.urls import include
from rest_framework_swagger.views import get_swagger_view
from sci_impact.views import index

schema_view = get_swagger_view(title='Impact App API')

# Customize the admin site
admin.site.site_header = " "
admin.site.site_title = "ImpactApp Admin Portal"
admin.site.index_title = "Welcome to ImpactApp"
admin.site.unregister(User)
admin.site.unregister(Group)

urlpatterns = [
    # root endpoint
    #re_path(r'', index),
    # api root endpoint
    re_path(r'^api/$', schema_view),
    # sci_impact api endpoints
    re_path(r'^api/sci_impact/', include('sci_impact.urls')),
    # admin view
    re_path(r'^admin/', admin.site.urls),
    # authentication
    re_path(r'^api-auth/', include('rest_framework.urls')),
]

