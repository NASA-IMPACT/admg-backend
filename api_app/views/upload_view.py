from rest_framework.generics import CreateAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from api_app.serializers import ImageSerializer

class ImageUploadView(CreateAPIView):
    parser_class = (MultiPartParser,)
    serializer_class = ImageSerializer
