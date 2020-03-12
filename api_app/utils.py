from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema

from django.template.loader import render_to_string


ALL_STATUS_CODE = ["200", "201", "202", "203", "204"]


class XcodeAutoSchema(SwaggerAutoSchema):

    def __init__(self, view, path, method, components, request, overrides, operation_keys=None):
        super().__init__(view, path, method, components, request, overrides)

    # used if redoc is used instead of swaggerui
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
    #         'x-code-samples': [
    #             {
    #                 "lang": "curl",
    #                 "source": render_to_string(
    #                     'curl_sample.html',
    #                     template_context
    #                 )
    #             },
    #             {
    #                 "lang": "python",
    #                 "source": render_to_string(
    #                     'python_sample.html',
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
