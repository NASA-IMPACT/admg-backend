import pytest

from django.contrib.contenttypes.models import ContentType

from data_models.models import PartnerOrg

from .models import CREATED_CODE, Change, ApprovalLog


@pytest.mark.django_db
class TestChange:
    def test_create_change_object(self):
        model_to_query = PartnerOrg
        content_type = ContentType.objects.get_for_model(model_to_query)

        change = Change.objects.create(
            content_type=content_type, status=0, action="Create"
        )

        change = Change.objects.filter(uuid=change.uuid).first()

        assert change.status == CREATED_CODE
        assert change.action == "Create"

    def test_approval_log_for_newly_created_change(self):
        model_to_query = PartnerOrg
        content_type = ContentType.objects.get_for_model(model_to_query)

        change = Change.objects.create(
            content_type=content_type, status=0, action="Create"
        )

        approval = ApprovalLog.objects.get(change=change)

        assert approval.change.status == CREATED_CODE
        assert approval.change == change
        assert approval.action == ApprovalLog.CREATE
