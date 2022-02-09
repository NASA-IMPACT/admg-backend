from drf_yasg import openapi

from rest_framework import permissions
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from oauth2_provider.contrib.rest_framework import TokenHasScope

from admg_webapp.users.models import ADMIN, STAFF
from ..models import ApprovalLog, Change
from ..serializers import ApprovalLogSerializer, ChangeSerializer
from .view_utils import handle_exception


def _validate_update(request, uuid):
    instance = Change.objects.get(uuid=uuid)
    # the change object can only be changed in pending or in_progress state
    if instance.status == Change.Statuses.PUBLISHED:
        raise Exception("Change has already been published. Make a new change request")
    return instance


class ApprovalLogListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = [STAFF]

    queryset = ApprovalLog.objects.all()
    serializer_class = ApprovalLogSerializer

    @handle_exception
    def get(self, request, *args, **kwargs):
        self.queryset = ApprovalLog.objects.filter(**request.query_params.dict())
        return super().get(request, *args, **kwargs)


class ChangeListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = [STAFF]

    queryset = Change.objects.all()
    serializer_class = ChangeSerializer

    @handle_exception
    def get(self, request, *args, **kwargs):
        self.queryset = Change.objects.filter(**request.query_params.dict())
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
    properties={"notes": openapi.Schema(type=openapi.TYPE_STRING)},
)


class ChangeValidationView(APIView):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = [STAFF]

    @handle_exception
    def post(self, request, *args, **kwargs):
        uuid = kwargs.get("uuid")
        instance = _validate_update(request, uuid)
        return instance.validate()


class ChangeSubmitView(APIView):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = [STAFF]

    @handle_exception
    def post(self, request, *args, **kwargs):
        instance = Change.objects.get(uuid=kwargs.get("uuid"))
        response = instance.submit(user=request.auth.user, notes=request.data.get("notes", ""))
        return Response(response)


class ChangeClaimView(APIView):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = [STAFF]

    @handle_exception
    def post(self, request, *args, **kwargs):
        instance = Change.objects.get(uuid=kwargs.get("uuid"))
        response = instance.claim(user=request.auth.user, notes=request.data.get("notes", ""))
        return Response(response)


class ChangeUnclaimView(APIView):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = [STAFF]

    @handle_exception
    def post(self, request, *args, **kwargs):
        instance = Change.objects.get(uuid=kwargs.get("uuid"))
        response = instance.unclaim(user=request.auth.user, notes=request.data.get("notes", ""))
        return Response(response)


class ChangeReviewView(APIView):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = [STAFF]

    @handle_exception
    def post(self, request, *args, **kwargs):
        instance = Change.objects.get(uuid=kwargs.get("uuid"))
        response = instance.review(user=request.auth.user, notes=request.data.get("notes", ""))
        return Response(response)


class ChangeRejectView(APIView):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = [STAFF]

    @handle_exception
    def post(self, request, *args, **kwargs):
        instance = Change.objects.get(uuid=kwargs.get("uuid"))
        response = instance.reject(user=request.auth.user, notes=request.data.get("notes", ""))
        return Response(response)


class ChangePublishView(APIView):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = [ADMIN]

    @handle_exception
    def post(self, request, *args, **kwargs):
        instance = Change.objects.get(uuid=kwargs.get("uuid"))
        response = instance.publish(user=request.auth.user, notes=request.data.get("notes", ""))
        return Response(response)
