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


def extract_response_details(original_data):
    """This function allows the extraction of the original message
    and data so they can be used by the handle_exception wrapper instead
    of being overwritten or left blank

    Args:
        original_data (dict/list): This should be a dict or a list

    Returns:
        success, message, data [bool, str, list]
    """

    if isinstance(original_data, dict):
        data = original_data.get('data', [])
        message = original_data.get('message', '')
        success = original_data.get('success', True)
    else:
        data = original_data
        message = ''
        success = True

    return success, message, data


def handle_exception(function):
    """
    Decorator function for handing error and returning data in the required
    format
    """

    def wrapper(self, request, *args, **kwargs):
        data = []
        message = ""
        success = True
        try:
            res = function(self, request, *args, **kwargs)
            if 300 >= res.status_code >= 200:
                original_data = res.data
                print(original_data)
                success, message, data = extract_response_details(original_data)
              
        except Exception as e:
            success = False
            try:
                message = json.dumps(e.get_full_details())
            except AttributeError:
                message = str(e)

        return JsonResponse({
            "success": success,
            "message": message,
            "data": data
        })
    return wrapper
