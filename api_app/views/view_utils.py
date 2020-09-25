from django.http import JsonResponse
from rest_framework.response import Response
from ..models import Change, UPDATE, CREATE, PATCH

"""
    Always use requires_admin_approval after handle_exception as it will catch the
    exceptions from requires_admin_approval as well
"""


def requires_admin_approval(model_name, action=UPDATE):
    def outer_wrapper(function):
        # unsed function variable because this adds request to the change model
        def inner_wrapper(self, request, *args, **kwargs):
            # validate data before creating the change object.
            # the drf implementation does these checks and creates the object from the same function
            # hence it could not be reused properly
            if action == CREATE:
                # the user should still be able to add in few partial fields
                serializer = self.get_serializer(data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
            elif action == UPDATE:
                partial = action == PATCH or kwargs.pop('partial', False)
                instance = self.get_object()
                serializer = self.get_serializer(instance, data=request.data, partial=partial)
                serializer.is_valid(raise_exception=True)

            change_object = Change(
                model_name=model_name,
                update=request.data,
                model_instance_uuid=kwargs.get("uuid"),
                action=action,
                user=request.user
            )
            change_object.save()
            return JsonResponse({
                'success': True,
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
        data = []
        message = ""
        success = True

        try:
            res = function(self, request, *args, **kwargs)
            if 300 >= res.status_code >= 200:
                data = res.data
        # TODO: change this to some custom exception
        except Exception as e:
            success = False
            message = str(e)

        return JsonResponse({
            "success": success,
            "message": message,
            "data": data
        })
    return wrapper
