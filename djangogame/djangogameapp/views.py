from datetime import datetime

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework.parsers import JSONParser

from djangogameapp.models import Snippet
from djangogameapp.serializers import SnippetSerializer

def index(request):
   now = datetime.now()

   html_content = "<html><head><title>Hello, Django</title></head><body>"
   html_content += "<strong>Hello Django!</strong> on " + now.strftime("%A, %d %B, %Y at %X")
   html_content += "</body></html>"

   return HttpResponse(html_content)

@csrf_exempt
def snippet_list(request):
    """
    List all code snippets, or create a new snippet.
    """
    if request.method == 'GET':
        snippets = Snippet.objects.all()
        serializer = SnippetSerializer(snippets, many=True)
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = SnippetSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)