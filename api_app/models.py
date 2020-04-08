import uuid

from django.apps import apps
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.timezone import now

from admg_webapp.users.models import User, ADMIN

PENDING = 'Pending'
APPROVED = 'Approved'
REJECTED = 'Rejected'
AVAILABLE_STATUSES = ((1, PENDING), (2, APPROVED), (3, REJECTED))


def false_success(message):
    return {
        "success": False,
        "message": message,
    }


def handle_approve_reject(function):
    def wrapper(self, admin_user, notes, first_change):
        """
        Decorator for handle or reject changes in the change table that
        1.) handles model_instance check
        2.) handles user role check
        3.) adds timestamps, approved/rejected_by user, notes to the change model
        4.) Saves the change model

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

        # if this is not the first change and there is no model_instance
        if not first_change and not self.model_instance:
            return false_success("The model name was not linked to any existing model")

        # approving user
        if admin_user.get_role_display() != ADMIN:
            return false_success("Only admin can approve a change")

        # raise error from used functions
        function(self, admin_user)

        self.appr_reject_by = admin_user
        self.notes = notes
        self.appr_reject_date = now()
        self.save()

        return {"success": True}

    return wrapper


class Change(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    added_date = models.DateTimeField(auto_now_add=True)
    appr_reject_date = models.DateTimeField()

    model_name = models.CharField(max_length=20, blank=False, null=False)
    status = models.IntegerField(choices=AVAILABLE_STATUSES, default=2)
    update = JSONField()
    model_instance_uuid = models.UUIDField(blank=False, null=False)
    model_instance = None

    first_change = models.BooleanField(default=False)
    # makes sense to set it null when the user is deleted, but doesn't make sense if it is null
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='changed_by', null=False
    )
    appr_reject_by = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, related_name='approved_by', null=True
    )
    notes = models.CharField(max_length=500, blank=True)

    def save(self, *args, **kwargs):
        if not self.model_instance:
            # no try catch because want it to fail if something goes wrong
            Model = apps.get_model('data_models', self.model_name)
            if self.first_change:
                self.model_instance = Model.create(**self.update)
            else:
                self.model_instance = Model.objects.get(uuid=model_instance_uuid)
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

        # first try to change in the model
        self.model_instance.update(**self.update)

        # if everything goes well
        self.status = 2  # approved

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

        self.status = 3  # rejected
