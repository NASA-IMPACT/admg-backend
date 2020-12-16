from uuid import uuid4

from django.apps import apps
from django.db import models
from django.utils.timezone import now
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from data_models import serializers as sz
from admg_webapp.users.models import User, ADMIN

CREATE = "Create"
UPDATE = "Update"
DELETE = "Delete"
PATCH = "Patch"


# The change is in progress, can not be approved, but the user can update the change request
IN_PROGRESS, IN_PROGRESS_CODE = "In Progress", 1

# Can be approved or rejected. Rejection sends it back to the in_progress state
PENDING, PENDING_CODE = "Pending", 2

# Once approved the changes in the change table is refected to the model
# The state of the change object can not be changed from this state.
APPROVED, APPROVED_CODE = "Approved", 3
AVAILABLE_STATUSES = (
    (PENDING_CODE, PENDING),
    (APPROVED_CODE, APPROVED),
    (IN_PROGRESS_CODE, IN_PROGRESS),
)


def false_success(message):
    return {"success": False, "message": message}


def handle_approve_reject(function):
    def wrapper(self, admin_user, notes):
        """
        Decorator to handle or reject changes in the change table that
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

        if self.status != PENDING_CODE:
            return false_success("The change is not in pending state.")

        # raise error from used functions
        updated = function(self, admin_user, notes)

        # a false success might be triggered, and using not doesn't rule out None
        if updated.get("success") == False:
            return updated

        self.status = updated["status"]  # approved/rejected
        self.appr_reject_by = admin_user
        self.notes = notes
        self.appr_reject_date = now()
        self.save(post_save=True)

        return {
            "success": True,
            "updated_model": self.model_name,
            "action": self.action,
            "uuid_changed": updated["uuid"],
            "status": self.get_status_display(),
        }

    return wrapper


class Change(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    model_instance_uuid = models.UUIDField(default=uuid4, blank=False, null=True)
    content_object = GenericForeignKey("content_type", "model_instance_uuid")

    added_date = models.DateTimeField(auto_now_add=True)
    appr_reject_date = models.DateTimeField(null=True, blank=True)

    status = models.IntegerField(choices=AVAILABLE_STATUSES, default=IN_PROGRESS_CODE)
    update = models.JSONField(default=dict, blank=True)
    previous = models.JSONField(default=dict)

    action = models.CharField(
        max_length=10,
        choices=((choice, choice) for choice in [CREATE, UPDATE, DELETE, PATCH]),
        default=CREATE,
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="changed_by", null=True, blank=True
    )
    appr_reject_by = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, related_name="approved_by", null=True, blank=True
    )
    notes = models.CharField(max_length=500, blank=True)

    @property
    def model_name(self):
        # TODO: Verify that this works with API
        cls = self.content_type.model_class()
        return cls.__name__ if cls else 'UNKNOWN'

    def __str__(self):
        return f"{self.model_name} >> {self.uuid}"

    def _check_model_and_uuid(self):
        """
        The method will raise loud errors if the model doesn't exist
        or the uuid deosn't exist in case of edit/delete change
        """
        model = apps.get_model("data_models", self.model_name)
        if self.action != CREATE:
            serializer_class = getattr(sz, f"{self.model_name}Serializer")
            instance = model.objects.get(uuid=self.model_instance_uuid)
            if self.action == UPDATE:
                serializer = serializer_class(instance)
                self.previous = {
                    key: serializer.data.get(key) for key in self.update
                }

    def save(self, *args, post_save=False, **kwargs):
        # do not check for validity of model_name and uuid if it has been approved or rejected.
        # Check is done for the first time only
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
        serializer_class = getattr(sz, f"{self.model_name}Serializer")
        model = apps.get_model("data_models", self.model_name)
        if self.action == CREATE:
            serializer = serializer_class(data=self.update)
            if serializer.is_valid():
                created = serializer.save()
                return {"uuid": created.uuid, "status": APPROVED_CODE}
            return false_success(serializer.errors)

        if not self.model_instance_uuid:
            return false_success("UUID for the model was not found")

        # filter because delete and update both work on filter, update doesn't work on get
        model_instance = model.objects.get(uuid=self.model_instance_uuid)
        if self.action == DELETE:
            model_instance.delete()
        else:
            # if not create or delete it is update, allow partial updates by default
            serializer = serializer_class(
                model_instance, data=self.update, partial=True
            )
            if serializer.is_valid():
                serializer.save()
        return {"uuid": self.model_instance_uuid, "status": APPROVED_CODE}

    @handle_approve_reject
    def reject(self, admin_user, notes):
        """
        Rejects a change. The change is not reflected in the model.
        Instead the change object is pushed to in_progress state
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

        return {"uuid": self.model_instance_uuid, "status": IN_PROGRESS_CODE}
