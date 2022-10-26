# to run this test file, use 'pytest -k api_app'

import json

import pytest
from django.contrib.contenttypes.models import ContentType

from admg_webapp.users.models import ADMIN_CODE, STAFF_CODE, User
from data_models.tests import factories
from ..models import ApprovalLog, Change


@pytest.mark.django_db
@pytest.mark.parametrize("factory", factories.DATAMODELS_FACTORIES)
class TestChange:
    @staticmethod
    def dump_logs(change):
        """if a test throws a hard to diagnose error, you can use this to dump
        logs for closer examination"""
        logs = [str(log) for log in ApprovalLog.objects.filter(change=change)]
        json.dump(logs, open("pytest_change_model_approval_logs.json", "w"))

    @staticmethod
    def create_users():
        staff_user = User.objects.create(role=STAFF_CODE, username="staff")
        staff_user_2 = User.objects.create(role=STAFF_CODE, username="staff_2")
        admin_user = User.objects.create(role=ADMIN_CODE, username="admin")
        admin_user_2 = User.objects.create(role=ADMIN_CODE, username="admin_2")
        return admin_user, admin_user_2, staff_user, staff_user_2

    @staticmethod
    def make_create_change_object(factory, custom_fields={}):
        """make a Change.Actions.CREATE change object to use during testing"""
        content_type = ContentType.objects.get_for_model(factory._meta.model)

        # _meta.fields does not contain many to many
        model_field_names = {
            field.name
            for field in factory._meta.get_model_class()._meta._forward_fields_map.values()
        }
        overrides = {
            field: value for field, value in custom_fields.items() if field in model_field_names
        }

        return Change.objects.create(
            content_type=content_type,
            status=Change.Statuses.CREATED,
            action="Create",
            update={**factory.as_change_dict(), **overrides},
        )

    @staticmethod
    def make_update_change_object(factory, create_draft, fields_to_keep=[]):
        """make a Change.Actions.CREATE change object to use during testing"""
        content_type = ContentType.objects.get_for_model(factory._meta.model)

        # we want the ability to keep the original's values, say short_name or concept_id
        # models can't take any field though, so this checks that the fields are real
        # TODO: move this to an error check?
        model_field_names = {
            field.name
            for field in factory._meta.get_model_class()._meta._forward_fields_map.values()
        }
        overrides = {
            field: create_draft.update[field]
            for field in fields_to_keep
            if field in model_field_names
        }

        return Change.objects.create(
            content_type=content_type,
            status=Change.Statuses.CREATED,
            action="Update",
            model_instance_uuid=create_draft.uuid,
            update={**factory.as_change_dict(), **overrides},
        )

    def test_change_query_check(self, factory):
        """test that nothing strange is happening between creating and querying a change object"""
        change = self.make_create_change_object(factory)
        change_query = Change.objects.filter(uuid=change.uuid).first()

        assert change == change_query

    def test_make_create_change_object(self, factory):
        """test that a freshly created object has the correct code"""
        change = self.make_create_change_object(factory)

        assert change.status == Change.Statuses.CREATED
        assert change.action == "Create"

    def test_approval_log_for_newly_created_change(self, factory):
        """test that creating a create change object generates the appropriate log"""
        change = self.make_create_change_object(factory)
        approval_log = ApprovalLog.objects.get(change=change)

        assert approval_log.change == change
        assert approval_log.change.status == Change.Statuses.CREATED
        assert approval_log.action == ApprovalLog.Actions.CREATE

    def test_normal_workflow(self, factory):
        admin_user, _, staff_user, staff_user_2 = self.create_users()

        # create
        change = self.make_create_change_object(factory)
        approval_log = change.get_latest_log()
        assert change.status == Change.Statuses.CREATED
        assert approval_log.action == ApprovalLog.Actions.CREATE
        # a user will be assigned if this action is made in the admin
        # however no user is assigned when this action is taken from the tests
        assert approval_log.user is None

        # edit
        change.update["short_name"] = "test_short_name"
        change.save()
        approval_log = change.get_latest_log()
        assert approval_log.action == ApprovalLog.Actions.EDIT
        assert approval_log.user is None
        assert change.status == Change.Statuses.IN_PROGRESS

        # submit
        change.submit(staff_user)
        approval_log = change.get_latest_log()
        assert approval_log.action == ApprovalLog.Actions.SUBMIT
        assert approval_log.user == staff_user
        assert change.status == Change.Statuses.AWAITING_REVIEW

        # claim
        change.claim(staff_user_2)
        approval_log = change.get_latest_log()
        assert approval_log.action == ApprovalLog.Actions.CLAIM
        assert approval_log.user == staff_user_2
        assert change.status == Change.Statuses.IN_REVIEW

        # reject
        notes = "rejection notes"
        change.reject(staff_user_2, notes=notes)
        approval_log = change.get_latest_log()
        assert approval_log.action == ApprovalLog.Actions.REJECT
        assert approval_log.notes == notes
        assert approval_log.user == staff_user_2
        assert change.status == Change.Statuses.IN_PROGRESS

        # submit
        change.submit(staff_user)
        approval_log = change.get_latest_log()
        assert approval_log.action == ApprovalLog.Actions.SUBMIT
        assert approval_log.user == staff_user
        assert change.status == Change.Statuses.AWAITING_REVIEW

        # claim
        change.claim(staff_user_2)
        approval_log = change.get_latest_log()
        assert approval_log.action == ApprovalLog.Actions.CLAIM
        assert approval_log.user == staff_user_2
        assert change.status == Change.Statuses.IN_REVIEW

        # review
        change.review(staff_user_2)
        approval_log = change.get_latest_log()
        assert approval_log.action == ApprovalLog.Actions.REVIEW
        assert approval_log.user == staff_user_2
        assert change.status == Change.Statuses.AWAITING_ADMIN_REVIEW

        # claim
        change.claim(admin_user)
        approval_log = change.get_latest_log()
        assert approval_log.action == ApprovalLog.Actions.CLAIM
        assert approval_log.user == admin_user
        assert change.status == Change.Statuses.IN_ADMIN_REVIEW

        # publish
        change.publish(admin_user)
        approval_log = change.get_latest_log()
        assert approval_log.action == ApprovalLog.Actions.PUBLISH
        assert approval_log.user == admin_user
        assert change.status == Change.Statuses.PUBLISHED

    def test_staff_cant_trash_untrash(self, factory):
        """check that error is thrown when staff member tries to trash or untrash an object"""
        admin_user, _, staff_user, _ = self.create_users()

        change = self.make_create_change_object(factory)
        change.update["short_name"] = "test_short_name"
        change.save()

        response = change.trash(staff_user, notes="trash")
        assert response["success"] is False
        assert response["message"] == "action failed because initiating user was not admin"

        change.trash(admin_user, notes="trash")

        response = change.untrash(staff_user)
        assert response["success"] is False
        assert response["message"] == "action failed because initiating user was not admin"

    def test_published_cant_be_trash(self, factory):
        """check that error is thrown when admin tries to trash a published item"""
        admin_user, _, _, _ = self.create_users()

        change = self.make_create_change_object(factory)
        change.update["short_name"] = "test_short_name"
        change.save()
        change.publish(admin_user)

        response = change.trash(admin_user, notes="trash")
        assert response["success"] is False
        assert (
            response["message"]
            == "action failed because status was not one of ['Created', 'In Progress', 'Awaiting Review', 'In Review', 'Awaiting Admin Review', 'In Admin Review']"
        )

    def test_staff_cant_publish(self, factory):
        """check that error is thrown when staff member tries to publish or claim awaiting admin review"""
        admin_user, _, staff_user, staff_user_2 = self.create_users()

        change = self.make_create_change_object(factory)
        change.update["short_name"] = "test_short_name"
        change.save()
        change.submit(staff_user)
        change.claim(staff_user_2)
        change.review(staff_user_2)

        response = change.claim(staff_user)
        assert response["success"] is False
        assert response["message"] == "action failed because initiating user was not admin"
        change.claim(admin_user)
        response = change.publish(staff_user)
        assert response["success"] is False
        assert response["message"] == "action failed because initiating user was not admin"

    def test_only_claim_awaiting(self, factory):
        """test that the claim function throws errors if not used on AWAITING objects"""
        admin_user, _, staff_user, staff_user_2 = self.create_users()

        change = self.make_create_change_object(factory)
        change.update["short_name"] = "test_short_name"
        change.save()

        # can't claim IN PROGRESS
        response = change.claim(staff_user)
        assert response["success"] is False
        assert (
            response["message"]
            == "action failed because status was not one of ['Awaiting Review', 'Awaiting Admin Review']"
        )
        response = change.claim(admin_user)
        assert response["success"] is False
        assert (
            response["message"]
            == "action failed because status was not one of ['Awaiting Review', 'Awaiting Admin Review']"
        )

        change.submit(staff_user)
        change.claim(staff_user_2)

        # can't claim IN REVIEW
        response = change.claim(staff_user)
        assert response["success"] is False
        assert (
            response["message"]
            == "action failed because status was not one of ['Awaiting Review', 'Awaiting Admin Review']"
        )
        response = change.claim(admin_user)
        assert response["success"] is False
        assert (
            response["message"]
            == "action failed because status was not one of ['Awaiting Review', 'Awaiting Admin Review']"
        )

        change.review(staff_user_2)
        change.claim(admin_user)

        # can't claim IN ADMIN REVIEW
        response = change.claim(staff_user)
        assert response["success"] is False
        assert (
            response["message"]
            == "action failed because status was not one of ['Awaiting Review', 'Awaiting Admin Review']"
        )
        response = change.claim(admin_user)
        assert response["success"] is False
        assert (
            response["message"]
            == "action failed because status was not one of ['Awaiting Review', 'Awaiting Admin Review']"
        )

        change.publish(admin_user)

        # can't claim PUBLISHED
        response = change.claim(staff_user)
        assert response["success"] is False
        assert (
            response["message"]
            == "action failed because status was not one of ['Awaiting Review', 'Awaiting Admin Review']"
        )
        response = change.claim(admin_user)
        assert response["success"] is False
        assert (
            response["message"]
            == "action failed because status was not one of ['Awaiting Review', 'Awaiting Admin Review']"
        )

    def test_admin_unclaim_all(self, factory):
        """test that admin can unclaim items claimed by other members"""
        admin_user, admin_user_2, staff_user, staff_user_2 = self.create_users()

        change = self.make_create_change_object(factory)
        change.update["short_name"] = "test_short_name"
        change.save()
        change.submit(staff_user)
        change.claim(staff_user_2)

        # test admin can unclaim in reviewing
        response = change.unclaim(admin_user)
        approval_log = change.get_latest_log()
        assert response["success"] is True
        assert change.status == Change.Statuses.AWAITING_REVIEW
        assert approval_log.action == ApprovalLog.Actions.UNCLAIM

        change.claim(staff_user_2)
        change.review(staff_user_2)
        change.claim(admin_user)

        # test admin can unclaim another admin's IN ADMIN REVIEW
        response = change.unclaim(admin_user_2)
        approval_log = change.get_latest_log()
        assert response["success"] is True
        assert change.status == Change.Statuses.AWAITING_ADMIN_REVIEW
        assert approval_log.action == ApprovalLog.Actions.UNCLAIM

    def test_staff_cant_unclaim_unowned(self, factory):
        """test that staff can't unclaim items they didn't claim"""
        admin_user, _, staff_user, staff_user_2 = self.create_users()

        change = self.make_create_change_object(factory)
        change.update["short_name"] = "test_short_name"
        change.save()
        change.submit(staff_user)
        change.claim(staff_user_2)

        # test staff can't unclaim in reviewing they didnt' claim
        response = change.unclaim(staff_user)
        approval_log = change.get_latest_log()
        assert response["success"] is False
        assert change.status == Change.Statuses.IN_REVIEW
        assert approval_log.action == ApprovalLog.Actions.CLAIM

        change.claim(staff_user_2)
        change.review(staff_user_2)
        change.claim(admin_user)

        # test staff can unclaim an admin's IN ADMIN REVIEW
        response = change.unclaim(staff_user)
        approval_log = change.get_latest_log()
        assert response["success"] is False
        assert change.status == Change.Statuses.IN_ADMIN_REVIEW
        assert approval_log.action == ApprovalLog.Actions.CLAIM

    def test_unpublished_unpublished(self, factory):
        admin_user, _, _, _ = self.create_users()
        change = self.make_create_change_object(factory)
        change.publish(admin_user)

        update = self.make_update_change_object(factory, change.uuid)

        update = Change
        change_2 = self.make_create_change_object(factory)

        change


@pytest.mark.django_db
@pytest.mark.parametrize(
    "endpoint",
    [
        "platform_type",
        "home_base",
        "repository",
        "focus_area",
        "season",
        "measurement_style",
        "measurement_type",
        "measurement_region",
        "geographical_region",
        "geophysical_concept",
        "campaign",
        "platform",
        "instrument",
        "deployment",
        "iop",
        "significant_event",
        "partner_org",
        "collection_period",
        "gcmd_phenomenon",
        "gcmd_project",
        "gcmd_platform",
        "gcmd_instrument",
        "alias",
    ],
)
class TestApi:
    def test_get(self, client, endpoint):
        response = client.get(f"/api/{endpoint}", headers={"Content-Type": "application/json"})
        assert response.status_code == 200
        response_dict = response.json()
        assert response_dict == {"success": True, "message": "", "data": []}

    def test_post_arent_public(self, client, endpoint):
        response = client.post(
            f"/api/{endpoint}", data={}, headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401
        response_dict = response.json()
        assert response_dict == {"detail": "Authentication credentials were not provided."}
