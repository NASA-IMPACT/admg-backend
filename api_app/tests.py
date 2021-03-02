import json

import pytest
from admg_webapp.users.models import User, ADMIN_CODE, STAFF_CODE
from data_models.models import PartnerOrg
from django.contrib.contenttypes.models import ContentType

from api_app.models import (AWAITING_ADMIN_REVIEW, AWAITING_ADMIN_REVIEW_CODE,
                            AWAITING_REVIEW, AWAITING_REVIEW_CODE, CREATED,
                            CREATED_CODE, IN_ADMIN_REVIEW,
                            IN_ADMIN_REVIEW_CODE, IN_PROGRESS,
                            IN_PROGRESS_CODE, IN_REVIEW, IN_REVIEW_CODE,
                            PUBLISHED, PUBLISHED_CODE, ApprovalLog, Change)


@pytest.mark.django_db
class TestChange:
    @staticmethod
    def dump_logs(change):
        """if a test throws a hard to diagnose error, you can use this to dump
        logs for closer examination"""
        logs = [str(log) for log in ApprovalLog.objects.filter(change=change)]
        json.dump(logs, open('pytest_change_model_approval_logs.json', 'w'))


    @staticmethod
    def create_users():
        staff_user = User.objects.create(role=STAFF_CODE, username='staff')
        staff_user_2 = User.objects.create(role=STAFF_CODE, username='staff_2')
        admin_user = User.objects.create(role=ADMIN_CODE, username='admin')
        admin_user_2 = User.objects.create(role=ADMIN_CODE, username='admin_2')
        return admin_user, admin_user_2, staff_user, staff_user_2


    @staticmethod
    def make_create_change_object():
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
        admin_user, _, staff_user, staff_user_2 = self.create_users()

        # create
        change = self.make_create_change_object()
        approval_log = change.get_latest_log()
        assert change.status == CREATED_CODE
        assert approval_log.action == ApprovalLog.CREATE
        assert approval_log.user is None

        # edit
        change.update['short_name'] = 'test_short_name'
        change.save()
        approval_log = change.get_latest_log()
        assert change.status == IN_PROGRESS_CODE
        assert approval_log.action == ApprovalLog.EDIT
        assert approval_log.user is None

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
        """check that error is thrown when staff member tries to publish or claim awaiting admin review"""
        admin_user, _, staff_user, staff_user_2 = self.create_users()

        change = self.make_create_change_object()
        change.update['short_name'] = 'test_short_name'
        change.save()
        change.submit(staff_user)
        change.claim(staff_user_2)
        change.review(staff_user_2)

        response = change.claim(staff_user)
        assert response['success'] is False
        assert response['message'] == 'action failed because initiating user was not admin'
        change.claim(admin_user)
        response = change.publish(staff_user)
        assert response['success'] is False
        assert response['message'] == 'action failed because initiating user was not admin'  


    def test_only_claim_awaiting(self):
        """test that the claim function throws errors if not used on AWAITING objects"""
        admin_user, _, staff_user, staff_user_2 = self.create_users()

        change = self.make_create_change_object()
        change.update['short_name'] = 'test_short_name'
        change.save()

        # can't claim IN PROGRESS
        response = change.claim(staff_user)
        assert response['success'] is False
        assert response['message'] == 'action failed because status was not one of [2, 4]'
        response = change.claim(admin_user)
        assert response['success'] is False
        assert response['message'] == 'action failed because status was not one of [2, 4]'

        change.submit(staff_user)
        change.claim(staff_user_2)

        # can't claim IN REVIEW
        response = change.claim(staff_user)
        assert response['success'] is False
        assert response['message'] == 'action failed because status was not one of [2, 4]'
        response = change.claim(admin_user)
        assert response['success'] is False
        assert response['message'] == 'action failed because status was not one of [2, 4]'

        change.review(staff_user_2)
        change.claim(admin_user)

        # can't claim IN ADMIN REVIEW
        response = change.claim(staff_user)
        assert response['success'] is False
        assert response['message'] == 'action failed because status was not one of [2, 4]'
        response = change.claim(admin_user)
        assert response['success'] is False
        assert response['message'] == 'action failed because status was not one of [2, 4]'

        change.publish(admin_user)

        # can't claim PUBLISHED
        response = change.claim(staff_user)
        assert response['success'] is False
        assert response['message'] == 'action failed because status was not one of [2, 4]'
        response = change.claim(admin_user)
        assert response['success'] is False
        assert response['message'] == 'action failed because status was not one of [2, 4]'


    def test_admin_unclaim_all(self):
        """test that admin can unclaim items claimed by other members"""
        admin_user, admin_user_2, staff_user, staff_user_2 = self.create_users()

        change = self.make_create_change_object()
        change.update['short_name'] = 'test_short_name'
        change.save()
        change.submit(staff_user)
        change.claim(staff_user_2)

        # test admin can unclaim in reviewing
        response = change.unclaim(admin_user)
        approval_log = change.get_latest_log()
        assert response['success'] is True
        assert change.status == AWAITING_REVIEW_CODE
        assert approval_log.action == ApprovalLog.UNCLAIM

        change.claim(staff_user_2)
        change.review(staff_user_2)
        change.claim(admin_user)

        # test admin can unclaim another admin's IN ADMIN REVIEW
        response = change.unclaim(admin_user_2)
        approval_log = change.get_latest_log()
        assert response['success'] is True
        assert change.status == AWAITING_ADMIN_REVIEW_CODE
        assert approval_log.action == ApprovalLog.UNCLAIM


    def test_staff_cant_unclaim_unowned(self):
        """test that staff can't unclaim items they didn't claim"""
        admin_user, _, staff_user, staff_user_2 = self.create_users()

        change = self.make_create_change_object()
        change.update['short_name'] = 'test_short_name'
        change.save()
        change.submit(staff_user)
        change.claim(staff_user_2)

        # test staff can't unclaim in reviewing they didnt' claim
        response = change.unclaim(staff_user)
        approval_log = change.get_latest_log()
        assert response['success'] is False
        assert change.status == IN_REVIEW_CODE
        assert approval_log.action == ApprovalLog.CLAIM

        change.claim(staff_user_2)
        change.review(staff_user_2)
        change.claim(admin_user)

        # test staff can unclaim an admin's IN ADMIN REVIEW
        response = change.unclaim(staff_user)
        approval_log = change.get_latest_log()
        assert response['success'] is False
        assert change.status == IN_ADMIN_REVIEW_CODE
        assert approval_log.action == ApprovalLog.CLAIM
