from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from rest_framework import permissions, serializers
from rest_framework.generics import (
    ListAPIView,
    RetrieveUpdateAPIView
)
from rest_framework.response import Response
from rest_framework.views import APIView

from oauth2_provider.contrib.rest_framework import TokenHasScope


from admg_webapp.users.models import ADMIN, STAFF
from ..models import Change, APPROVED, REJECTED
from ..serializers import ChangeSerializer
from .view_utils import handle_exception

APPROVE = 'approve'
REJECT = 'reject'


class ChangeListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = [ADMIN]

    queryset = Change.objects.all()
    serializer_class = ChangeSerializer

    @handle_exception
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ChangeListUpdateView(RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = [STAFF]

    lookup_field = "uuid"
    queryset = Change.objects.all()
    serializer_class = ChangeSerializer

    @handle_exception
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @handle_exception
    def put(self, request, *args, **kwargs):
        instance = Change.objects.get(uuid=kwargs.get("uuid"))
        if instance.user.pk != request.user.pk:
            raise Exception("Only owner of the object can change it.")
        if instance.get_status_text() == APPROVED:
            raise Exception("This has already been approved.")
        return super().put(request, *args, **kwargs)

    @handle_exception
    def patch(self, request, *args, **kwargs):
        instance = Change.objects.get(uuid=kwargs.get("uuid"))
        if instance.user.pk != request.user.pk:
            raise Exception("Only owner of the object can change it.")
        if instance.get_status_text() == APPROVED:
            raise Exception("This has already been approved.")
        return super().patch(request, *args, **kwargs)


notes_param = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=["username"],
    properties={
        "notes": openapi.Schema(type=openapi.TYPE_STRING)
    },
)


# this is only for the swagger UI and has no significance in the code
class ChangeResponseSerializer(serializers.Serializer):
    action = serializers.CharField(
        help_text=f"Action Type. One of: {APPROVE}, {REJECT}",
        min_length=6
    )
    change_object_uuid = serializers.CharField(
        help_text="The uuid that was changed",
        min_length=36
    )


def ChangeApproveRejectView(approve_or_reject):
    """
    returns a view based on given parameter

    Args:
        approve_or_reject(string): One of approve or reject

    Returns:
        view class.as_view()
    """

    class View(APIView):
        permission_classes = [permissions.IsAuthenticated, TokenHasScope]
        required_scopes = [ADMIN]

        @swagger_auto_schema(
            request_body=notes_param,
            responses={"201": ChangeResponseSerializer}
        )
        @handle_exception
        def post(self, request, *args, **kwargs):
            uuid = kwargs.get("uuid")
            instance = Change.objects.get(uuid=uuid)

            if approve_or_reject == APPROVE:
                if instance.get_status_text() == APPROVED:
                    raise Exception("This has already been approved.")

                res = instance.approve(request.user, request.data.get("notes", "approved"))
                return Response(data={
                    "action": approve_or_reject,
                    "action_info": res
                })
            elif approve_or_reject == REJECT:
                if instance.get_status_text() == REJECTED:
                    raise Exception("This has already been rejected.")

                res = instance.reject(request.user, request.data.get("notes", "rejected"))
                return Response(data={
                    "action": approve_or_reject,
                    "action_info": res,
                })

    return View.as_view()
