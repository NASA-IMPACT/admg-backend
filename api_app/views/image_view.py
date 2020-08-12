from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView
from rest_framework.parsers import JSONParser, MultiPartParser

from api_app.serializers import ImageSerializer
from data_models.models import Image

from ..models import DELETE
from .view_utils import handle_exception, requires_admin_approval


class ImageListCreateAPIView(ListCreateAPIView):
    """
        List images and create an image object
    """
    
    parser_class = (MultiPartParser, JSONParser)
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

class ImageRetrieveDestroyAPIView(RetrieveDestroyAPIView):
    """
        Retrieve a single image and delete images
    """
    
    parser_class = (MultiPartParser, JSONParser)
    serializer_class = ImageSerializer
    lookup_field = "uuid"
    queryset = Image.objects.all()

    @handle_exception
    @requires_admin_approval(model_name='Image', action=DELETE)
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
