from django.apps import apps
from django.db.models import Q

from rest_framework import permissions
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, GenericAPIView

from oauth2_provider.contrib.rest_framework import TokenHasScope
from data_models import serializers as sz
from admg_webapp.users.models import User
from .view_utils import handle_exception, requires_admin_approval
from ..models import Change

from data_models.models import (
    GcmdInstrument,
    GcmdPhenomenon,
    GcmdProject,
    GcmdPlatform,
)


class NotificationSidebar:
    def get_gcmd_count(self):
        return (
            Change.objects.of_type(GcmdInstrument, GcmdPlatform, GcmdProject, GcmdPhenomenon)
            .filter(Q(recommendation__submitted=False) | Q(status__lte=5))
            .distinct("uuid")
            .count()
        )

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "gcmd_changes_count": self.get_gcmd_count(),
        }


class GetPermissionsMixin(GenericAPIView):
    def get_permissions(self):
        if self.request.method == "GET":
            self.permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        else:
            self.permission_classes = [permissions.IsAuthenticated, TokenHasScope]
            self.required_scopes = [User.Roles.STAFF.label]
        return super().get_permissions()


def GenericCreateGetAllView(model_name):
    """
    Creates a view for LIST and CREATE for given model name

    Args:
        model_name (string) : model_name must be one from data_models/models.py

    Returns:
        View(class) : view class for LIST and CREATE API views
    """

    class View(NotificationSidebar, GetPermissionsMixin, ListCreateAPIView):
        Model = apps.get_model("data_models", model_name)
        queryset = Model.objects.all()
        serializer_class = getattr(sz, f"{model_name}Serializer")

        @handle_exception
        def get(self, request, *args, **kwargs):
            params = request.query_params.dict()
            try:
                self.queryset = self.Model.search(params)
            except (NotImplementedError, AttributeError):
                self.queryset = self.queryset.filter(**params)
            res = super().get(request, *args, **kwargs)
            return res

        @handle_exception
        @requires_admin_approval(model_name=model_name, action=Change.Actions.CREATE)
        def post(self, request, *args, **kwargs):
            return super().post(request, *args, **kwargs)

    return View.as_view()


def GenericPutPatchDeleteView(model_name):
    """
    Creates a view for PUT, PATCH and DELETE for given model name

    Args:
        model_name (string) : model_name must be one from data_models/models.py

    Returns:
        View(class) : view class for PUT, PATCH and DELETE API views
    """

    class View(NotificationSidebar, GetPermissionsMixin, RetrieveUpdateDestroyAPIView):
        Model = apps.get_model("data_models", model_name)
        lookup_field = "uuid"
        queryset = Model.objects.all()
        serializer_class = getattr(sz, f"{model_name}Serializer")

        @handle_exception
        def get(self, request, *args, **kwargs):
            return super().get(request, *args, **kwargs)

        @handle_exception
        @requires_admin_approval(model_name=model_name)
        def put(self, request, *args, **kwargs):
            return super().put(request, *args, **kwargs)

        @handle_exception
        @requires_admin_approval(model_name=model_name, action=Change.Actions.UPDATE)
        def patch(self, request, *args, **kwargs):
            return super().patch(request, *args, **kwargs)

        @handle_exception
        @requires_admin_approval(model_name=model_name, action=Change.Actions.DELETE)
        def delete(self, request, *args, **kwargs):
            return super().delete(request, *args, **kwargs)

    return View.as_view()
