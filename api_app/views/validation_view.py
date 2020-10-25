from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, GenericAPIView

from data_models import serializers as data_models_serializers

from api_app.serializers import ValidationSerializer
from api_app.models import Change

from ..models import DELETE
from .view_utils import handle_exception, requires_admin_approval


class ValidationView(GenericAPIView):#CreateAPIView):
    """
        List images and create an image object
    """
    validation_serializer = ValidationSerializer

    @handle_exception
    def post(self, request, *args, **kwargs):
        # TODO: there needs to be some error handling for if the request is missing these things
        model_name = request.data['model_name']
        data = request.data['data']
        partial = request.data['partial']

        serializer_class = getattr(data_models_serializers, f"{model_name}Serializer")
        serializer_obj = serializer_class(data=data, partial=partial)

        # if validation fails, the code ends here.
        # TODO: add custom validation?
        validation_results = serializer_obj.is_valid(raise_exception=True)

        return Response(
            status=200,
            data={
                'message':'All serializer validations passed',
            }
        )
