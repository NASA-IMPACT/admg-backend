from rest_framework import serializers
from .models import DummyModel


class DummySerializer(serializers.ModelSerializer):
    class Meta:
        model = DummyModel
        fields = ('test1', 'test2', 'test3')
