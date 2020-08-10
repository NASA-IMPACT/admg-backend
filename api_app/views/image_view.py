from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView
from rest_framework.parsers import MultiPartParser

from api_app.serializers import ImageSerializer
from data_models.models import Image

from ..models import DELETE
from .view_utils import handle_exception, requires_admin_approval


class ImageListCreateAPIView(ListCreateAPIView):
    """
        Lists images and creates an image object
    """
    
    parser_class = (MultiPartParser,)
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

class ImageRetrieveDestroyAPIView(RetrieveDestroyAPIView):
    """
        Retrieve a single image and delete images
    """
    
    parser_class = (MultiPartParser,)
    serializer_class = ImageSerializer
    lookup_field = "uuid"
    queryset = Image.objects.all()

    @handle_exception
    @requires_admin_approval(model_name='Image', action=DELETE)
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
