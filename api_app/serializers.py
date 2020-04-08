from rest_framework import serializers
from .models import Change


class ChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Change
        fields = (
            "uuid",
            "added_date",
            "appr_reject_date",
            "model_name",
            "status",
            "update",
            "model_instance_uuid",
            "first_change",
            "user",
            "appr_reject_by",
            "notes",
        )

        read_only_fields = ['appr_reject_date', 'appr_reject_by', 'status']
