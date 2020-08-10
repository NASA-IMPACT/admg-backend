from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView
from rest_framework.parsers import MultiPartParser

from api_app.serializers import ImageSerializer

from ..models import DELETE
from .view_utils import handle_exception, requires_admin_approval

from data_models.models import Image


# class ImageUploadView(ListCreateAPIView):
class ImageListCreateView(ListCreateAPIView):
    parser_class = (MultiPartParser,)
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

class ImageRetrieveDestroyView(RetrieveDestroyAPIView):
    parser_class = (MultiPartParser,)
    serializer_class = ImageSerializer

    @handle_exception
    @requires_admin_approval(model_name='Image', action=DELETE)
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
