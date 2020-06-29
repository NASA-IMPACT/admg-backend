from rest_framework import serializers

from api_app.models import Change
from data_models.models import Image


class ChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Change
        fields = "__all__"
        read_only_fields = ["appr_reject_date", "appr_reject_by", "status"]


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = "__all__"
