import json

from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema

from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.http import HttpResponse

from oauth2_provider.views.base import TokenView
from oauth2_provider.models import get_access_token_model
from oauth2_provider.signals import app_authorized

from admg_webapp.users.models import ADMIN, STAFF

ALL_STATUS_CODE = ["200", "201", "202", "203", "204"]


class XcodeAutoSchema(SwaggerAutoSchema):

    def __init__(self, view, path, method, components, request, overrides, operation_keys=None):
        super().__init__(view, path, method, components, request, overrides)

    # used if redoc is used instead of swaggerui
    # from django.template.loader import render_to_string
    # def get_operation(self, operation_keys=None):
    #     operation = super().get_operation(operation_keys)

    #     # Using django templates to generate the code
    #     request_url = self.request._request.build_absolute_uri(self.path)
    #     request_url = request_url.replace("%7Bid%7D", "id")
    #     template_context = {
    #         "request_url": request_url,
    #         "method": self.method,
    #     }
    #     print(template_context)
    #     operation.update({
    #         "x-code-samples": [
    #             {
    #                 "lang": "curl",
    #                 "source": render_to_string(
    #                     "curl_sample.html",
    #                     template_context
    #                 )
    #             },
    #             {
    #                 "lang": "python",
    #                 "source": render_to_string(
    #                     "python_sample.html",
    #                     template_context
    #                 )
    #             }
    #         ]
    #     })
    #     return operation

    def _response_schema(self, prev_schema):
        return openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "data": prev_schema,
                "message": openapi.Schema(
                    type="string",
                    description="What went wrong"
                ),
                "sucess": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Was the API successfull?"
                )
            }
        )

    def get_responses(self):
        """
        Updates response schema so it suits following structure:

        {
            "data": data_response
            "success": true/false,
            "message": "what went wrong"
        }
        """

        r = super().get_responses()

        for status_code in ALL_STATUS_CODE:
            if r.get(status_code):
                if r[status_code].get("schema"):
                    r[status_code]["schema"] = self._response_schema(r[status_code]["schema"])

        return r


class CustomTokenView(TokenView):
    """
    used by /authenticate/token/
    appends scopes to the token based on uer roles
    """

    @method_decorator(sensitive_post_parameters("password", "username"))
    def post(self, request, *args, **kwargs):
        _, headers, body, status = self.create_token_response(request)
        if status == 200:
            access_token = json.loads(body).get("access_token")
            if access_token is not None:
                token = get_access_token_model().objects.get(
                    token=access_token
                )

                # add role based scope in the token
                role = token.user.get_role_display()
                scope = ["read", "write", role]
                if role == ADMIN:
                    scope.append(STAFF)
                token.scope = " ".join(scope)
                token.save()

                app_authorized.send(
                    sender=self, request=request,
                    token=token
                )
        response = HttpResponse(content=body, status=status)

        for k, v in headers.items():
            response[k] = v
        return response
