from uuid import uuid4

from django.apps import apps
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.timezone import now

from admg_webapp.users.models import User, ADMIN

CREATE = 'Create'
UPDATE = 'Update'
DELETE = 'Delete'

PENDING, PENDING_CODE = "Pending", 1
APPROVED, APPROVED_CODE = "Approved", 2
REJECTED, REJECTED_CODE = "Rejected", 3
AVAILABLE_STATUSES = ((PENDING_CODE, PENDING), (APPROVED_CODE, APPROVED), (REJECTED_CODE, REJECTED))


def false_success(message):
    return {
        "success": False,
        "message": message,
    }


def handle_approve_reject(function):
    def wrapper(self, admin_user, notes):
        """
        Decorator for handle or reject changes in the change table that
        1.) handles user role check
        2.) adds timestamps, approved/rejected_by user, notes to the change model
        3.) Saves the change model

        Args:
            function (function) : decorated function
            admin_user (User) : The admin user that approved or rejected the change
            notes (string) : Notes provided by the admin user

        Returns:
            dict : {
                success: True/false,
                message: "In case success is false"
            }
        """

        # approving user
        if admin_user.get_role_display() != ADMIN:
            return false_success("Only admin can approve a change")

        # raise error from used functions
        updated = function(self, admin_user, notes)

        self.appr_reject_by = admin_user
        self.notes = notes
        self.appr_reject_date = now()
        self.save(post_save=True)

        return {
            "success": True,
            "updated_model": self.model_name,
            "action": self.action,
            "uuid_changed": updated["uuid"],
        }

    return wrapper


class Change(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    added_date = models.DateTimeField(auto_now_add=True)
    appr_reject_date = models.DateTimeField(null=True)

    model_name = models.CharField(max_length=20, blank=False, null=False)
    status = models.IntegerField(choices=AVAILABLE_STATUSES, default=PENDING_CODE)
    update = JSONField()
    model_instance_uuid = models.UUIDField(default=uuid4, blank=False, null=True)

    action = models.CharField(
        max_length=10,
        choices=((CREATE, CREATE), (UPDATE, UPDATE), (DELETE, DELETE)),
        default=UPDATE
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="changed_by", null=True
    )
    appr_reject_by = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, related_name="approved_by", null=True
    )
    notes = models.CharField(max_length=500, blank=True)

    def _check_model_and_uuid(self):
        """
        The method will raise loud errors if the model doesn't exist
        or the uuid deosn't exist in case of edit/delete change
        """
        Model = apps.get_model("data_models", self.model_name)
        if self.action != CREATE:
            Model.objects.get(uuid=self.model_instance_uuid)

    def save(self, *args, post_save=False, **kwargs):
        # do not check it has been approved or rejected
        # check only the first time
        if not post_save:
            self._check_model_and_uuid()
        return super().save(*args, **kwargs)

    @handle_approve_reject
    def approve(self, admin_user, notes):
        """
        Approves a change. The change is reflected in the model.
        The user checks are taken care by the decorator
        Return is taken care of by the decorator

        Args:
            admin_user (User):
                the admin_user that approves the change.
                This is not an unused variable. The decorator uses it
            notes (string):
                Extra notes that were provided by the approving/rejecting admin
                This is not an unused variable. The decorator uses it

        Returns:
            (dict): {
                success: True/False,
                message: "In case success is False"
            }
        """

        Model = apps.get_model("data_models", self.model_name)
        if self.action == CREATE:
            created = Model.objects.create(**self.update)
            self.status = 2  # approved
            return {"uuid": created.uuid}

        if not self.model_instance_uuid:
            return false_success("UUID for the model was not found")

        # filter because delete and update both work on filter, update doesn't work on get
        model_instance = Model.objects.filter(uuid=self.model_instance_uuid)
        updated = {"uuid": self.model_instance_uuid}

        if self.action == DELETE:
            model_instance.delete()
        else:
            # first try to change in the model
            model_instance.update(**self.update)

        # if everything goes well
        self.status = APPROVED_CODE  # approved
        return updated

    @handle_approve_reject
    def reject(self, admin_user, notes):
        """
        Rejects a change. The change is reflected in the model.
        The user checks are taken care by the decorator
        Return is taken care of by the decorator

        Args:
            admin_user (User):
                the admin_user that approves the change.
                This is not an unused variable. The decorator uses it
            notes (string):
                Extra notes that were provided by the approving/rejecting admin
                This is not an unused variable. The decorator uses it

        Returns:
            (dict): {
                success: True/False,
                message: "In case success is False"
            }
        """

        self.status = REJECTED_CODE  # rejected
        return {"uuid": self.model_instance_uuid}
