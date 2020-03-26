from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView

from drf_yasg import openapi

from ..serializers import DummyModel, DummySerializer

'''
Custom request parameters to yasg
request_category_post = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['test1', 'test2'],
    properties={
        'test1': openapi.Schema(
            type=openapi.TYPE_STRING,
            title='Id',
            readOnly=True,
            description='Id of the category'
        ),
        'test2': openapi.Schema(
            type=openapi.TYPE_STRING,
            title='Category',
            maxLength=200,
            minLength=1,
            description='Name of the category'
        )
    },
    example={
        'test1': "test",
        'test2': 'Business',
    }
)

request_category_get = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=[],
    properties={
        'test1': openapi.Schema(
            type=openapi.TYPE_STRING,
            title='Id',
            readOnly=True,
            description='Id of the category'
        ),
        'test2': openapi.Schema(
            type=openapi.TYPE_STRING,
            title='Category',
            maxLength=200,
            minLength=1,
            description='Name of the category'
        )
    },
    example=openapi.Response('Response example', DummySerializer)
)

responses = {
    '200': DummySerializer,
    '400': 'Bad Request',
    '404': 'Not found'
}
'''

class DummyAPIListCreate(ListCreateAPIView):
    queryset = DummyModel.objects.all()
    serializer_class = DummySerializer


class DummyAPIRetrieveUpdateDelete(RetrieveUpdateDestroyAPIView):
    queryset = DummyModel.objects.all()
    serializer_class = DummySerializer
