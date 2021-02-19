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
from ..models import Change, IN_PROGRESS_CODE, IN_REVIEW_CODE, IN_ADMIN_REVIEW_CODE, PUBLISHED_CODE
from ..serializers import ChangeSerializer
from .view_utils import handle_exception

APPROVE = 'approve'
REJECT = 'reject'


def is_admin(user):
    # TODO: consider refactor to combine with models.py is_admin()
    return user.get_role_display() == ADMIN


def _validate_update(request, uuid):
    instance = Change.objects.get(uuid=uuid)
    # if request.user.get_role_display() != ADMIN and instance.user.pk != request.user.pk:
    #     raise Exception("Only admin or the owner of the object can update the change request.")
    # the change object can only be changed in pending or in_progress state
    if instance.status == PUBLISHED_CODE:
        raise Exception("Change has already been published. Make a new change request")
    return instance


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

    @handle_exception
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @handle_exception
    def put(self, request, *args, **kwargs):
        _validate_update(request, kwargs.get("uuid"))
        return super().put(request, *args, **kwargs)

    @handle_exception
    def patch(self, request, *args, **kwargs):
        _validate_update(request, kwargs.get("uuid"))
        return super().patch(request, *args, **kwargs)


notes_param = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=[],
    properties={
        "notes": openapi.Schema(type=openapi.TYPE_STRING)
    },
)

# TODO: rewrite this
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

class ChangeValidationView(APIView):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = [STAFF]

    @handle_exception
    def post(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        instance = _validate_update(request, uuid)
        return instance.validate()

class ChangeSubmitView(APIView):
    # TODO: is this going to add the dates and all that other metadata?
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = [STAFF]

    @handle_exception
    def post(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        instance = _validate_update(request, uuid)
        instance.validate()
        instance.status = IN_REVIEW_CODE
        instance.save()
        return Response(f"Status for uuid: {uuid} changed to 'In Review'.")

class ChangeReviewView(APIView):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = [STAFF]

    @handle_exception
    def post(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        instance = _validate_update(request, uuid)
        instance.validate()
        instance.status = IN_ADMIN_REVIEW_CODE
        instance.save()
        return Response(f"Status for uuid: {uuid} changed to 'In Admin Review'.")


class ChangePublishView(APIView):
    class View(APIView):
        permission_classes = [permissions.IsAuthenticated, TokenHasScope]
        required_scopes = [ADMIN]

        @handle_exception
        def post(self, request, *args, **kwargs):
            uuid = kwargs.get('uuid')
            instance = Change.objects.get(uuid=uuid)

            res = instance.approve(request.user, request.data.get('notes', 'approved'))
            return Response(data={
                'action': 'published',
                'action_info': res
            })


class ChangeRejectView(APIView):
    class View(APIView):
        permission_classes = [permissions.IsAuthenticated, TokenHasScope]
        required_scopes = [STAFF]

        @handle_exception
        def post(self, request, *args, **kwargs):
            uuid = kwargs.get('uuid')
            instance = Change.objects.get(uuid=uuid)

            # only a change in the pending state can be approved or rejected
            if instance.status not in [IN_REVIEW_CODE, IN_ADMIN_REVIEW_CODE]:
                raise Exception("Change is not in review and cannot be rejected.")

            if instance.status == IN_ADMIN_REVIEW_CODE and not(is_admin(request.user)):
                raise Exception("Only admin users can reject object in admin review")


            notes = request.data.get('notes')
            if not notes:
                raise Exception("Notes required for rejection.")
            res = instance.reject(request.user, notes)
            return Response(data={
                'action': 'rejected',
                'action_info': res,
            })
