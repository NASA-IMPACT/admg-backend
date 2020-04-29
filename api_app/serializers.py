from rest_framework import serializers
from .models import Change


class ChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Change
        fields = "__all__"
        read_only_fields = ["appr_reject_date", "appr_reject_by", "status"]
