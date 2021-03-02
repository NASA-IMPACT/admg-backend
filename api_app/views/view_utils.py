import json

from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from rest_framework.response import Response

from ..models import UPDATE, Change

"""
    Always use requires_admin_approval after handle_exception as it will catch the
    exceptions from requires_admin_approval as well
"""


def requires_admin_approval(model_name, action=UPDATE):
    def outer_wrapper(function):
        # unsed function variable because this adds request to the change model
        def inner_wrapper(self, request, *args, **kwargs):

            content_type = ContentType.objects.get(app_label="data_models", model=model_name.lower())

            change_object = Change(
                content_type=content_type,
                update=request.data,
                model_instance_uuid=kwargs.get("uuid"),
                action=action,
                user=request.user
            )
            change_object.save()

            return Response({
                'uuid': change_object.uuid,
                'message': f'Change request with uuid: {change_object.uuid} created for the given request'
            })

        return inner_wrapper
    return outer_wrapper


def handle_exception(function):
    """
    Decorator function for handing error and returning data in the required
    format
    """
    def wrapper(self, request, *args, **kwargs):
        try:
            original_response = function(self, request, *args, **kwargs)

        except Exception as e:
            try:
                message = json.dumps(e.get_full_details())
            except AttributeError:
                message = str(e)

            return JsonResponse({
                "success": False,
                "message": message
            })
        return original_response
    return wrapper
