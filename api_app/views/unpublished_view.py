from rest_framework.generics import ListAPIView

from api_app.serializers import UnpublishedSerializer

from ..models import Change
from .view_utils import handle_exception
from .generic_views import GetPermissionsMixin


class UnpublishedChangesView(GetPermissionsMixin, ListAPIView):
    """
    Lists unpublished changes with certain status and action
    """

    queryset = Change.objects.filter(
        status=Change.Statuses.IN_ADMIN_REVIEW, action=Change.Actions.CREATE
    )
    serializer_class = UnpublishedSerializer

    @handle_exception
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
