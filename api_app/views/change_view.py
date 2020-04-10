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
from ..models import Change, PENDING_CODE, APPROVED_CODE
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
        self.queryset = Change.objects.filter(
            **request.query_params.dict()
        )
        return super().get(request, *args, **kwargs)


class ChangeListUpdateView(RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = [STAFF]

    lookup_field = "uuid"
    queryset = Change.objects.all()
    serializer_class = ChangeSerializer

    def _validate_update(self, request, uuid):
        instance = Change.objects.get(uuid=uuid)
        if request.user.get_role_display() != ADMIN or instance.user.pk != request.user.pk:
            raise Exception("Only admin or the owner of the object can update the change request.")
        # the change object can only be changed in pending or in_progress state
        if instance.status == APPROVED_CODE:
            raise Exception("Change has already been approved. Make a new change request")

    @handle_exception
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @handle_exception
    def put(self, request, *args, **kwargs):
        self._validate_update(request, kwargs.get("uuid"))
        return super().put(request, *args, **kwargs)

    @handle_exception
    def patch(self, request, *args, **kwargs):
        self._validate_update(request, kwargs.get("uuid"))
        return super().patch(request, *args, **kwargs)


notes_param = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=[],
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

            # only a change in the pending state can be approved or rejected
            if instance.status != PENDING_CODE:
                raise Exception("Change is not in pending state.")

            if approve_or_reject == APPROVE:
                res = instance.approve(request.user, request.data.get("notes", "approved"))
                return Response(data={
                    "action": approve_or_reject,
                    "action_info": res
                })
            elif approve_or_reject == REJECT:
                notes = request.data.get("notes")
                if not notes:
                    raise Exception("Notes required for rejection.")
                res = instance.reject(request.user, )
                return Response(data={
                    "action": approve_or_reject,
                    "action_info": res,
                })

    return View.as_view()
