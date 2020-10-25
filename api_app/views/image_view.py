from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView
from rest_framework.parsers import MultiPartParser

from api_app.serializers import ImageSerializer
from data_models.models import Image

from ..models import DELETE
from .view_utils import handle_exception, requires_admin_approval


class ImageListCreateAPIView(ListCreateAPIView):
    """
        List images and create an image object
    """

    parser_class = (MultiPartParser,)
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

    @handle_exception
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @handle_exception
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

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
