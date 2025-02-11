import json

from admg_webapp.users.models import User
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema
from oauth2_provider.models import get_access_token_model
from oauth2_provider.signals import app_authorized
from oauth2_provider.views.base import TokenView

ALL_STATUS_CODE = ["200", "201", "202", "203", "204"]


def model_name_for_url(model_name) -> str:
    from api_app.urls import camel_to_snake

    return camel_to_snake(model_name)


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
                "message": openapi.Schema(type="string", description="What went wrong"),
                "sucess": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Was the API successfull?"
                ),
            },
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

        res = super().get_responses()

        for status_code in ALL_STATUS_CODE:
            if res.get(status_code):
                if res[status_code].get("schema"):
                    res[status_code]["schema"] = self._response_schema(res[status_code]["schema"])
                # this bit maps the description to the required format as well
                elif res[status_code].get("description"):
                    res[status_code]["schema"] = self._response_schema(
                        openapi.Schema(
                            type="string",
                            description=res[status_code].get("description"),
                        ),
                    )

        return res


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
                token = get_access_token_model().objects.get(token=access_token)

                # add role based scope in the token
                role = token.user.get_role_display()
                scope = ["read", "write", role]
                if role == User.Roles.ADMIN.label:
                    scope.append(User.Roles.STAFF.label)
                token.scope = " ".join(scope)
                token.save()

                app_authorized.send(sender=self, request=request, token=token)
        response = HttpResponse(content=body, status=status)

        for k, v in headers.items():
            response[k] = v
        return response
