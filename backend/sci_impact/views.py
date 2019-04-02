from django.http import HttpResponse, Http404
#from rest_framework.views import APIView
#from rest_framework.response import Response
from rest_framework import generics, viewsets, permissions
from sci_impact.models import Scientist
from sci_impact.serializers import ScientistSerializer


#def index(request):
#    return HttpResponse("Hello, this app aim at computing the impact of scientific publications.")

class ScientistViewSet(viewsets.ModelViewSet):
    """
    retrieve:
    Return the given scientist.

    list:
    Return a list of all the existing scientists.

    create:
    Create a new scientist instance.

    delete:
    Delete the given scientist.
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = Scientist.objects.all()
    serializer_class = ScientistSerializer
    http_method_names = ['get', 'post', 'head', 'delete']
