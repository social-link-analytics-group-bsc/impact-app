from rest_framework import viewsets, permissions
from sci_impact.models import Scientist, ScientificPublication
from sci_impact.serializers import ScientistSerializer, ScientificPublicationSerializer


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


class ScientificPublicationViewSet(viewsets.ModelViewSet):
    """
    retrieve:
    Return the given scientific publication.

    list:
    Return a list of all the existing scientific publication.

    create:
    Create a new scientific publication.

    delete:
    Delete the given scientific publication.
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = ScientificPublication.objects.all()
    serializer_class = ScientificPublicationSerializer
    http_method_names = ['get', 'post', 'head', 'delete']
