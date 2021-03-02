import pytest

from django.contrib.contenttypes.models import ContentType

from admg_webapp.users.models import User
from data_models.models import PartnerOrg

from api_app.models import (
    Change, ApprovalLog,
    CREATED, CREATED_CODE,
    IN_PROGRESS, IN_PROGRESS_CODE,
    AWAITING_REVIEW, AWAITING_REVIEW_CODE,
    IN_REVIEW, IN_REVIEW_CODE,
    AWAITING_ADMIN_REVIEW, AWAITING_ADMIN_REVIEW_CODE,
    IN_ADMIN_REVIEW, IN_ADMIN_REVIEW_CODE,
    PUBLISHED, PUBLISHED_CODE,
)

import json
import pytest


@pytest.mark.django_db
class TestChange:
    def dump_logs(self, change):
        """if a test throws a hard to diagnose error, you can use this to dump
        logs for closer examination"""
        logs = [str(log) for log in ApprovalLog.objects.filter(change=change)]
        json.dump(logs, open('pytest_change_model_approval_logs.json', 'w'))


    def create_users(self):
        staff_user = User.objects.create(role=0, username='staff')
        staff_user_2 = User.objects.create(role=0, username='staff_2')
        admin_user = User.objects.create(role=1, username='admin')
        return admin_user, staff_user, staff_user_2


    def make_create_change_object(self):
        """make a CREATE PartnerOrg change object to use during testing"""
        model_to_query = PartnerOrg
        content_type = ContentType.objects.get_for_model(model_to_query)

        return Change.objects.create(
            content_type=content_type, 
            status=CREATED_CODE, 
            action="Create"
        )


    def test_change_query_check(self):
        """test that nothing strange is happening between creating and querying a change object"""
        change = self.make_create_change_object()
        change_query =  Change.objects.filter(uuid=change.uuid).first()

        assert change == change_query


    def test_make_create_change_object(self):
        """test that a freshly created object has the correct code"""
        change = self.make_create_change_object()

        assert change.status == CREATED_CODE
        assert change.action == "Create"


    def test_approval_log_for_newly_created_change(self):
        """test that creating a create change object generates the appropriate log"""
        change = self.make_create_change_object()
        approval_log = ApprovalLog.objects.get(change=change)

        assert approval_log.change == change
        assert approval_log.change.status == CREATED_CODE
        assert approval_log.action == ApprovalLog.CREATE


    def test_normal_workflow(self):
        admin_user, staff_user, staff_user_2 = self.create_users()

        # create
        change = self.make_create_change_object()
        approval_log = change.get_latest_log()
        assert change.status == CREATED_CODE
        assert approval_log.action == ApprovalLog.CREATE
        assert approval_log.user == None

        # edit
        change.update['short_name'] = 'test_short_name'
        change.save()
        approval_log = change.get_latest_log()
        assert change.status == IN_PROGRESS_CODE
        assert approval_log.action == ApprovalLog.EDIT
        assert approval_log.user == None

        # submit
        change.submit(staff_user)
        approval_log = change.get_latest_log()
        assert change.status == AWAITING_REVIEW_CODE
        assert approval_log.action == ApprovalLog.SUBMIT
        assert approval_log.user == staff_user

        # claim
        change.claim(staff_user_2)
        approval_log = change.get_latest_log()
        assert change.status == IN_REVIEW_CODE
        assert approval_log.action == ApprovalLog.CLAIM
        assert approval_log.user == staff_user_2

        # reject
        notes = 'rejection notes'
        change.reject(staff_user_2, notes = notes)
        approval_log = change.get_latest_log()
        assert change.status == IN_PROGRESS_CODE
        assert approval_log.action == ApprovalLog.REJECT
        assert approval_log.notes == notes
        assert approval_log.user == staff_user_2

        # submit
        change.submit(staff_user)
        approval_log = change.get_latest_log()
        assert change.status == AWAITING_REVIEW_CODE
        assert approval_log.action == ApprovalLog.SUBMIT
        assert approval_log.user == staff_user

        # claim
        change.claim(staff_user_2)
        approval_log = change.get_latest_log()
        assert change.status == IN_REVIEW_CODE
        assert approval_log.action == ApprovalLog.CLAIM
        assert approval_log.user == staff_user_2

        # review
        change.review(staff_user_2)
        approval_log = change.get_latest_log()
        assert change.status == AWAITING_ADMIN_REVIEW_CODE
        assert approval_log.action == ApprovalLog.REVIEW
        assert approval_log.user == staff_user_2

        # claim
        change.claim(admin_user)
        approval_log = change.get_latest_log()
        assert change.status == IN_ADMIN_REVIEW_CODE
        assert approval_log.action == ApprovalLog.CLAIM
        assert approval_log.user == admin_user

        # publish
        change.publish(admin_user)
        approval_log = change.get_latest_log()
        assert change.status == PUBLISHED_CODE
        assert approval_log.action == ApprovalLog.PUBLISH
        assert approval_log.user == admin_user


    def test_staff_cant_publish(self):
        """check that error is thrown when staff member tries to publish"""
        pass


    def test_only_claim_awaiting(self):
        """test that the claim function throws errors if not used on AWAITING objects"""
        pass


    def test_admin_unclaim_all(self):
        """test that admin can unclaim items claimed by other members"""
        pass
    

    def test_staff_cant_unclaim_unowned(self):
        """test that staff can't unclaim items they didn't claim"""
        pass
