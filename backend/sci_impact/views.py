from django.http import HttpResponse, Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from sci_impact.models import Scientist
from sci_impact.serializers import ScientistSerializer
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse


#def index(request):
#    return HttpResponse("Hello, this app aim at computing the impact of scientific publications.")


#@api_view(['GET'])
#def api_root(request, format=None):
#    return Response({
#        'scientists': reverse('snippet-list', request=request, format=format)
#    })


class ScientistList(APIView):
    """
    List all scientists, or create a new scientist.
    """
    def get(self, request, format=None):
        snippets = Scientist.objects.all()
        serializer = ScientistSerializer(snippets, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = ScientistSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScientistDetail(APIView):
    """
    Retrieve, update or delete a snippet instance.
    """
    def get_object(self, pk):
        try:
            return Scientist.objects.get(pk=pk)
        except Scientist.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        snippet = self.get_object(pk)
        serializer = ScientistSerializer(snippet)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        snippet = self.get_object(pk)
        serializer = ScientistSerializer(snippet, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        snippet = self.get_object(pk)
        snippet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


