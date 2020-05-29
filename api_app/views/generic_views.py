from django.apps import apps

from rest_framework import permissions
from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView,
    ListCreateAPIView,
)

from oauth2_provider.contrib.rest_framework import TokenHasScope
from data_models import serializers as sz
from admg_webapp.users.models import STAFF
from .view_utils import handle_exception, requires_admin_approval
from ..models import CREATE, DELETE, PATCH


def GenericCreateGetAllView(model_name):
    """
    Creates a view for LIST and CREATE for given model name

    Args:
        model_name (string) : model_name must be one from data_models/models.py

    Returns:
        View(class) : view class for LIST and CREATE API views
    """
    class View(ListCreateAPIView):
        permission_classes = [permissions.IsAuthenticated, TokenHasScope]
        required_scopes = [STAFF]

        Model = apps.get_model('data_models', model_name)
        queryset = Model.objects.all()
        serializer_class = getattr(sz, f"{model_name}Serializer")

        @handle_exception
        def get(self, request, *args, **kwargs):
            self.queryset = self.Model.objects.filter(
                **request.query_params.dict()
            )
            res = super().get(request, *args, **kwargs)
            return res

        @handle_exception
        @requires_admin_approval(model_name=model_name, action=CREATE)
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
    class View(RetrieveUpdateDestroyAPIView):
        permission_classes = [permissions.IsAuthenticated, TokenHasScope]
        required_scopes = [STAFF]
        Model = apps.get_model('data_models', model_name)
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
        @requires_admin_approval(model_name=model_name, action=PATCH)
        def patch(self, request, *args, **kwargs):
            return super().patch(request, *args, **kwargs)

        @handle_exception
        @requires_admin_approval(model_name=model_name, action=DELETE)
        def delete(self, request, *args, **kwargs):
            return super().delete(request, *args, **kwargs)

    return View.as_view()
