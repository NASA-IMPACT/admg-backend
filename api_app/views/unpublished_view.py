from rest_framework.generics import ListCreateAPIView
from rest_framework.parsers import MultiPartParser

from api_app.serializers import UnpublishedSerializer

from ..models import Change
from .view_utils import handle_exception
from .generic_views import GetPermissionsMixin


class UnpublishedListCreateAPIView(GetPermissionsMixin, ListCreateAPIView):
    """
    List images and create an image object
    """

    parser_class = (MultiPartParser,)
    # filter(Q(income__gte=5000) | Q(income__isnull=True))
    queryset = Change.objects.filter(
        status=Change.Statuses.IN_ADMIN_REVIEW, action=Change.Actions.CREATE
    )
    serializer_class = UnpublishedSerializer

    @handle_exception
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @handle_exception
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
