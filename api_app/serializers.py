from data_models.models import Image
from rest_framework import serializers

from api_app.models import ApprovalLog, Change


class ChangeSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(read_only=True)

    class Meta:
        model = Change
        fields = "__all__"
        read_only_fields = ["status"]


class ApprovalLogSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(read_only=True)
    action_string = serializers.SerializerMethodField()

    def get_action_string(self, obj):
        return obj.get_action_display()

    class Meta:
        model = ApprovalLog
        fields = "__all__"


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = "__all__"


class UnpublishedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Change
        fields = ["update", "uuid"]


class ValidationSerializer(serializers.Serializer):
    model_name = serializers.CharField(help_text="String of the model name: Season", min_length=128)
    data = serializers.JSONField(
        help_text="""JSON containing model field names and values: {"short_name": "arctas"}"""
    )
    partial = serializers.BooleanField(
        help_text="Boolean indicating whether validation will be partial (missing required fields is allowed)"
    )
