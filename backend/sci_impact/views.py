from django.shortcuts import render
from rest_framework import viewsets, permissions
from sci_impact.models import Scientist, Article
from sci_impact.serializers import ScientistSerializer, ArticleSerializer


def index(request):
    return render(request, "home.html")


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


class ArticleViewSet(viewsets.ModelViewSet):
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
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    http_method_names = ['get', 'post', 'head', 'delete']
