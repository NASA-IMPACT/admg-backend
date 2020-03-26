from django.apps import apps
from django.http import JsonResponse

from rest_framework import permissions
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView
from oauth2_provider.contrib.rest_framework import TokenHasScope

import data_models.serializers as sz


def handle_exception(fn):
    """
    Decorator function for handing error and returning data in the required
    format
    """
    def wrapper(self, request, *args, **kwargs):
        data = []
        message = ""
        success = True
        try:
            res = fn(self, request, *args, **kwargs)
            if 300 >= res.status_code >= 200:
                data = res.data
        except Exception as e:
            success = False
            message = str(e)

        return JsonResponse({
            "success": success,
            "message": message,
            "data": data
        })
    return wrapper


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
        required_scopes = ["Staff"]

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
        def post(self, request, *args, **kwargs):
            return super().post(request, *args, **kwargs)

    return View


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
        required_scopes = ["Staff"]
        Model = apps.get_model('data_models', model_name)
        lookup_field = "uuid"
        queryset = Model.objects.all()
        serializer_class = getattr(sz, f"{model_name}Serializer")

        @handle_exception
        def put(self, request, *args, **kwargs):
            return super().put(request, *args, **kwargs)

        @handle_exception
        def patch(self, request, *args, **kwargs):
            return super().patch(request, *args, **kwargs)

        @handle_exception
        def delete(self, request, *args, **kwargs):
            return super().delete(request, *args, **kwargs)

    return View
