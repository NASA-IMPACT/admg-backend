from uuid import uuid4

from crum import get_current_user
from django.apps import apps
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import functions, expressions, aggregates
from django.db.models.fields.json import KeyTextTransform
from rest_framework.response import Response

from admg_webapp.users.models import ADMIN, User
from data_models import serializers


CREATE = "Create"
UPDATE = "Update"
DELETE = "Delete"
PATCH = "Patch"


# The change has been freshly ingested, but no one has made edits using the admin interface
CREATED, CREATED_CODE = "Created", 0

# The change is in progress, can not be approved, but the user can update the change request
IN_PROGRESS, IN_PROGRESS_CODE = "In Progress", 1

# The change has been added to the review pile, but hasn't been claimed
AWAITING_REVIEW, AWAITING_REVIEW_CODE = "Awaiting Review", 2

# The change as been claimed, and can now be can now be reviewed or rejected. Rejection sends it back to the in_progress state
IN_REVIEW, IN_REVIEW_CODE = "In Review", 3

# The change has been added to the admin review pile, but hasn't been claimed
AWAITING_ADMIN_REVIEW, AWAITING_ADMIN_REVIEW_CODE = "Awaiting Admin Review", 4

# Can be published or rejected. Rejection sends it back to the in_progress state
IN_ADMIN_REVIEW, IN_ADMIN_REVIEW_CODE = "In Admin Review", 5

# Once approved the changes in the change table is refected to the model
# The state of the change object can not be changed from this state.
PUBLISHED, PUBLISHED_CODE = "Published", 6

# The change has been moved to the trash
IN_TRASH, IN_TRASH_CODE = "In Trash", 7


AVAILABLE_STATUSES = (
    (CREATED_CODE, CREATED),
    (IN_PROGRESS_CODE, IN_PROGRESS),
    (AWAITING_REVIEW_CODE, AWAITING_REVIEW),
    (IN_REVIEW_CODE, IN_REVIEW),
    (AWAITING_ADMIN_REVIEW_CODE, AWAITING_ADMIN_REVIEW),
    (IN_ADMIN_REVIEW_CODE, IN_ADMIN_REVIEW),
    (PUBLISHED_CODE, PUBLISHED),
    (IN_TRASH_CODE, IN_TRASH)
)

def generate_failure_response(message):
    return {
        'success': False,
        'message': message
    }


def generate_success_response(status_str, data):
    return {
        "success": True,
        "message": f"Change object has been moved to the '{status_str}' stage.",
        "data": data
    }


def is_not_admin(user):
    """Returns None if user is admin, and a failure dictionary if user
    is not admin. Separation into a dedicated function allows usage inside
    the decorator or within the claim function.

    Args:
        user (User): User being evaluated for admin status

    Returns:
        [dict]: {success, message}
    """

    if user.get_role_display() != ADMIN:
        return generate_failure_response("action failed because initiating user was not admin")


def is_admin(function):
    def wrapper(self, user, notes="", **kwargs):

        if not_admin := is_not_admin(user):
            if not kwargs.get('doi'):
                return not_admin

        result = function(self, user, notes)

        return result
    return wrapper


def is_status(accepted_statuses_list):
    def decorator(function):
        def wrapper(self, user, notes=""):

            if self.status not in accepted_statuses_list:
                status_strings = [AVAILABLE_STATUSES[status][1] for status in accepted_statuses_list]
                return generate_failure_response(
                    f"action failed because status was not one of {status_strings}"
                )

            result = function(self, user, notes)

            return result
        return wrapper
    return decorator


class ApprovalLog(models.Model):
    """Keeps a log of the changes (publish, reject, etc) made to a particular draft"""

    TRASH = -1
    UNTRASH = 0
    CREATE = 1
    EDIT = 2
    SUBMIT = 3
    REVIEW = 4
    PUBLISH = 5
    REJECT = 6
    CLAIM = 7
    UNCLAIM = 8

    ACTION_CHOICES = [
        (TRASH, 'trash'),
        (UNTRASH, 'untrash'),
        (CREATE, 'create'),
        (EDIT, 'edit'),
        (SUBMIT, 'submit'),
        (REVIEW, 'review'),
        (PUBLISH, 'publish'),
        (REJECT, 'reject'),
        (CLAIM, 'claim'),
        (UNCLAIM, 'unclaim'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    change = models.ForeignKey('Change', on_delete=models.CASCADE, blank=True)

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="user",
        null=True,
        blank=True,
    )

    date = models.DateTimeField(auto_now_add=True)

    action = models.IntegerField(
        choices=ACTION_CHOICES,
        default=CREATE,
    )
    notes = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.user} | {self.get_action_display()} | {self.notes} | {self.date}"

    class Meta:
        ordering = ['-date']

    def get_action_display_past_tense(self):
        action = self.get_action_display()
        return f"{action}d" if action.endswith('e') else f"{action}ed"



class ChangeQuerySet(models.QuerySet):
    def of_type(self, *models):
        """
        Limit changes to only those targeted to provided models
        """
        return self.filter(content_type__model__in=[m._meta.model_name for m in models])

    def add_updated_at(self):
        """
        Add the date of the latest related ApprovalLog as a 'updated_at' attribute
        """
        return self.annotate(updated_at=aggregates.Max("approvallog__date"))

    def prefetch_approvals(self, *, order_by="-date", select_related=("user",)):
        """
        Prefetch the related approvallog_set with support for custom order_by
        and select_related
        """
        return self.prefetch_related(
            models.Prefetch(
                "approvallog_set",
                queryset=ApprovalLog.objects.order_by(order_by).select_related(
                    *select_related
                ),
            )
        )

    def annotate_from_relationship(
        self,
        of_type: models.Model,
        to_attr: str,
        uuid_from: str,
        identifier="short_name",
    ):
        """
        Annotate queryset with an identifier obtained from a related model.

        of_type:
            class of model that contains our desired identifier
        to_attr:
            attribute to where identifier will be annotated
        uuid_from:
            attribute in the "update" dict of source model that holds the uuid
            of the model to be joined
        identifier:
            attribute in the "update" dict of joined model that holds the identifier
        """
        uuid_dest_attr = f"{of_type._meta.model_name}_uuid"
        return self.annotate(
            **{
                uuid_dest_attr: functions.Cast(
                    functions.Coalesce(
                        functions.NullIf(
                            KeyTextTransform(uuid_from, "update"), expressions.Value("")
                        ),
                        # In the event that the Change model doesn't have the uuid_from property in its
                        # 'update' object, the operation to retrieve the value from the 'update' will return
                        # NULL. The DB will complain if we try to try to join a UUID on a NULL value, so in
                        # the event that the uuid_from key isn't present in the 'update' object, we use a
                        # dummy UUID fallback for the join which won't exist in the join table.
                        expressions.Value("00000000-0000-0000-0000-000000000000"),
                    ),
                    output_field=models.UUIDField(),
                ),
                to_attr: models.Subquery(
                    Change.objects.of_type(of_type)
                    .filter(
                        # NOTE: This only shows the first created short_name, but doesn't reflect updated short_names
                        action=CREATE,
                        uuid=expressions.OuterRef(uuid_dest_attr),
                    )
                    .values(f"update__{identifier}")[:1]
                ),
            },
        )

    def annotate_from_published(self, of_type, to_attr, identifier="short_name"):
        """
        Retrieve an identifier string from published model if possible, falling
        back to change model if no published model is available.

        of_type:
            class of model that contains our desired identifier
        to_attr:
            attribute to where identifier will be annotated
        identifier:
            attribute in the "update" dict of joined model that holds the identifier
        """
        return self.annotate(
            **{
                to_attr: functions.Coalesce(
                    expressions.Subquery(
                        (
                            of_type.objects.filter(uuid=expressions.OuterRef("uuid"))[
                                :1
                            ]
                        ).values(identifier)
                    ),
                    KeyTextTransform(identifier, "update"),
                    output_field=models.TextField(),
                )
            }
        )



class Change(models.Model):
    # use these field values when assigning the field status in the field_status_tracking dict
    FIELD_UNVIEWED = 1
    FIELD_INCORRECT = 2
    FIELD_UNSURE = 3
    FIELD_CORRECT = 4
    FIELD_DEFAULT = FIELD_UNVIEWED
    
    FIELD_STATUS_MAPPING = {
        FIELD_UNVIEWED: 'unviewed',
        FIELD_INCORRECT: 'incorrect',
        FIELD_UNSURE: 'unsure',
        FIELD_CORRECT: 'correct',
    }

    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    content_type = models.ForeignKey(
        ContentType,
        help_text="Model for which the draft pertains.",
        on_delete=models.CASCADE,
    )
    model_instance_uuid = models.UUIDField(default=uuid4, blank=True, null=True)
    content_object = GenericForeignKey("content_type", "model_instance_uuid")

    status = models.IntegerField(choices=AVAILABLE_STATUSES, default=IN_PROGRESS_CODE)
    update = models.JSONField(default=dict, blank=True)
    field_status_tracking = models.JSONField(default=dict, blank=True)
    previous = models.JSONField(default=dict)

    action = models.CharField(
        max_length=10,
        choices=((choice, choice) for choice in [CREATE, UPDATE, DELETE, PATCH]),
        default=UPDATE,
    )
    objects = ChangeQuerySet.as_manager()

    class Meta:
        verbose_name = "Draft"

    def get_field_status_str(self, field_status):
        """Gets the str value associated with each field status

        Args:
            field_status (int): Integer field status. Should be one of the
                built in statuses accessed through the model instance, such as
                Change.FIELD_UNSURE, or it should come from the field_status_tracking
                json

        Raises:
            ValueError: Throws a value error if the provided field_status is not one
                of the built in statuses.

        Returns:
            str: String value for the provided status integer
        """

        try:
            return self.FIELD_STATUS_MAPPING[field_status]
        except KeyError as E:
            raise KeyError('The field_status provided is not among the built statuses') from E

    def generate_field_status_tracking_dict(self):
        """
        Creates the field status tracking dictionary used to track whether a
        particular change object field has been looked at and found to be correct,
        incorrect, etc. This dictionary is meant to be wiped clean and recreated at
        different points in the change object's life cycle in order to allow more
        granularity in the review process.
        """

        source_model = self.content_type.model_class()
        self.field_status_tracking = {
            field.name: {'status': self.FIELD_DEFAULT, 'notes': ''} for field in source_model._meta.fields
        }

    @property
    def model_name(self):
        # TODO: Verify that this works with API
        cls = self.content_type.model_class()
        return cls.__name__ if cls else "UNKNOWN"

    def __str__(self):
        return f"{self.model_name} >> {self.uuid}"

    def _check_model_and_uuid(self):
        """
        The method will raise loud errors if the model doesn't exist
        or the uuid deosn't exist in case of edit/delete change
        """
        model = apps.get_model("data_models", self.model_name)
        if self.action != CREATE:
            serializer_class = getattr(serializers, f"{self.model_name}Serializer")
            instance = model.objects.get(uuid=self.model_instance_uuid)
            if self.action == UPDATE:
                serializer = serializer_class(instance)
                self.previous = {key: serializer.data.get(key) for key in self.update}

    def get_latest_log(self):
        return ApprovalLog.objects.filter(change=self).order_by('date').last()

    def save(self, *args, post_save=False, **kwargs):
        # do not check for validity of model_name and uuid if it has been approved or rejected.
        # Check is done for the first time only
        # post_save=False prevents self.previous from being set
        if not post_save:
            self._check_model_and_uuid()

        # change object was freshly created and has no logs
        if not ApprovalLog.objects.filter(change=self).exists():
            self.status = CREATED_CODE
            # the post_save function handles the creation of the approval log
        # should only log changes made to the draft while in progress
        elif self.status == CREATED_CODE:
            self.status = IN_PROGRESS_CODE

        if not self.field_status_tracking:
            self.generate_field_status_tracking_dict()

        return super().save(*args, **kwargs)

    def _run_validator(self, partial):
        """Helper function that runs the serializer validator. Please note
        that if errors are found, the error handler will capture them and this
        function's return will be bypassed.

        Args:
            partial (bool): A True value indicates partial validation, where
            required database fields are allowed to be missing.

        Returns:
            string: Returns a message string only if validation is passed.
        """

        serializer_class = getattr(serializers, f"{self.model_name}Serializer")
        serializer_obj = serializer_class(data=self.update, partial=partial)
        serializer_obj.is_valid(raise_exception=True)

        return 'All serializer validations passed'

    def validate(self):
        """Runs the serializer validation. Note that different request types will
        have partial or non-partial validation. If errors are found, the error
        handler will capture them and this function's return will be bypassed.

        Returns:
            Response: Returns a 200 with a validation message, only if the valdations
            pass. Otherwise, the error handler will print out each validation error string
            and error code.
        """
        if self.action == CREATE:
            validation_message = self._run_validator(partial=False)

        elif self.action == PATCH or self.action == UPDATE:
            validation_message = self._run_validator(partial=True)

        elif self.action == DELETE:
            validation_message = ''

        return Response(
            status=200,
            data={
                'message': validation_message,
            }
        )

    def _get_model_instance(self):
        model = apps.get_model("data_models", self.model_name)
        return model.objects.get(uuid=self.model_instance_uuid)

    def _save_serializer(self, model_instance, data, partial):
        serializer_class = getattr(serializers, f"{self.model_name}Serializer")
        serializer = serializer_class(instance=model_instance, data=data, partial=partial)

        if serializer.is_valid(raise_exception=True):
            new_model_instance = serializer.save()
            response = {"uuid": new_model_instance.uuid, "status": PUBLISHED_CODE}

        return response

    def _create(self):
        # set the db uuid == change request uuid
        self.update['uuid'] = str(self.uuid)

        response = self._save_serializer(
            model_instance=None,
            data=self.update,
            partial=False
        )

        return response

    def _update_patch(self):
        if not self.model_instance_uuid:
            response = {"success": False, "message": "UUID for the model was not found"}
        else:
            response = self._save_serializer(
                model_instance=self._get_model_instance(),
                data=self.update,
                partial=True
            )

        return response

    def _delete(self):
        if not self.model_instance_uuid:
            response = {"success": False, "message": "UUID for the model was not found"}
        else:
            model_instance = self._get_model_instance()
            model_instance.delete()

            response = {"uuid": self.model_instance_uuid, "status": PUBLISHED_CODE}

        return response

    @is_status([CREATED_CODE, IN_PROGRESS_CODE])
    def submit(self, user, notes=""):
        self.status = AWAITING_REVIEW_CODE

        ApprovalLog.objects.create(
            change = self,
            user = user,
            action = ApprovalLog.SUBMIT,
            notes = notes
        )

        self.save(post_save=True)

        return generate_success_response(
            status_str= AWAITING_REVIEW,
            data={
                "uuid": self.uuid,
                "status": AWAITING_REVIEW_CODE
            }
        )

    @is_status([IN_REVIEW_CODE])
    def review(self, user, notes=""):
        self.status = AWAITING_ADMIN_REVIEW_CODE
        ApprovalLog.objects.create(
            change = self,
            user = user,
            action = ApprovalLog.REVIEW,
            notes = notes
        )
        self.save(post_save=True)

        return generate_success_response(
            status_str=AWAITING_ADMIN_REVIEW,
            data={
                "uuid": self.uuid,
                "status": AWAITING_ADMIN_REVIEW_CODE
            }
        )


    @is_admin
    def publish(self, admin_user, notes=""):
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

        if self.action == CREATE:
            response = self._create()
        elif self.action == UPDATE or self.action == PATCH:
            response = self._update_patch()
        elif self.action == DELETE:
            response = self._delete()

        if response.get('success') == False:
            return response

        # links co to the new db instance
        # this is not what syncs the UUIDs
        if self.action == CREATE:
            self.model_instance_uuid = response['uuid']

        if self.status != IN_ADMIN_REVIEW_CODE:
            ApprovalLog.objects.create(
                change = self,
                user = admin_user,
                action = ApprovalLog.REVIEW,
                notes = notes
            )

        ApprovalLog.objects.create(
            change = self,
            user = admin_user,
            action = ApprovalLog.PUBLISH,
            notes = notes
        )

        self.status = PUBLISHED_CODE

        self.save(post_save=True)

        return generate_success_response(
            status_str=PUBLISHED,
            data={
                "updated_model": self.model_name,
                "action": self.action,
                "uuid_changed": response["uuid"],
                "status": PUBLISHED_CODE
            }
        )


    @is_admin
    @is_status([
        CREATED_CODE,
        IN_PROGRESS_CODE,
        AWAITING_REVIEW_CODE,
        IN_REVIEW_CODE,
        AWAITING_ADMIN_REVIEW_CODE,
        IN_ADMIN_REVIEW_CODE
    ])
    def trash(self, user, notes='', doi=False):
        """Moves a change object to the IN_TRASH stage. Expected use case
        is for DOIs which need to be ignored and items created accidently.
        Items can be removed from the trash with self.untrash()

        Args:
            user (User): User trashing the object
            notes (string): Extra notes that were provided by the trashing user. Default is ''.

        Returns:
            [dict]: {"success", "message", "data": {"uuid", "status"}}
        """

        self.status = IN_TRASH_CODE
        ApprovalLog.objects.create(
            change = self,
            user = user,
            action = ApprovalLog.TRASH,
            notes = notes
        )
        self.save(post_save=True)

        return generate_success_response(
            status_str=IN_TRASH,
            data={
                "uuid": self.uuid,
                "status": IN_TRASH_CODE
            }
        )


    @is_admin
    @is_status([IN_TRASH_CODE])
    def untrash(self, user, notes='', doi=False):
        """Moves a change object from trash to the in progress stage.

        Args:
            user (User): User untrashing the object
            notes (string): Extra notes that were provided by the untrashing user. Default is ''.

        Returns:
            [dict]: {"success", "message", "data": {"uuid", "status"}}
        """

        self.status = IN_PROGRESS_CODE
        ApprovalLog.objects.create(
            change = self,
            user = user,
            action = ApprovalLog.UNTRASH,
            notes = notes
        )
        self.save(post_save=True)

        return generate_success_response(
            status_str=IN_PROGRESS,
            data={
                "uuid": self.uuid,
                "status": IN_PROGRESS_CODE
            }
        )


    @is_status([IN_REVIEW_CODE, IN_ADMIN_REVIEW_CODE])
    def reject(self, user, notes):
        """
        Rejects a change. The change is not reflected in the model.
        Instead the change object is pushed to in_progress state
        The user checks are taken care by the decorator
        Return is taken care of by the decorator

        Args:
            user (User):
                the user that approves the change.
            notes (string):
                Extra notes that were provided by the approving/rejecting

        Returns:
            (dict): {
                success: True/False,
                message: "In case success is False"
            }
        """

        self.status = IN_PROGRESS_CODE
        ApprovalLog.objects.create(
            change = self,
            user = user,
            action = ApprovalLog.REJECT,
            notes = notes
        )
        self.save(post_save=True)

        return generate_success_response(
            status_str=IN_PROGRESS,
            data={
                "uuid": self.uuid,
                "status": IN_PROGRESS_CODE
            }
        )


    def _goto_next_approval_stage(self):
        """Do not call this, it is an internal function"""
        self.status += 1


    def _goto_previous_approval_stage(self):
        """Do not call this, it is an internal function"""
        self.status -= 1


    @is_status([AWAITING_REVIEW_CODE, AWAITING_ADMIN_REVIEW_CODE])
    def claim(self, user, notes=''):
        """Claims a change object for review or admin review for the given user 
        and updates the log.

        Args:
            user (User): User claiming the object for review or admin review
            notes (str, optional): Notes field. Defaults to ''.

        Returns:
            [dict]: {"success", "message", "data": {"uuid", "status"}}
        """

        # cannot use is_admin decorator for this check, because claim doesn't universally
        # require admin, only for one of the two statuses
        if self.status == AWAITING_ADMIN_REVIEW_CODE:
            if not_admin := is_not_admin(user):
                return not_admin

        self._goto_next_approval_stage()

        ApprovalLog.objects.create(
            change = self,
            user = user,
            action = ApprovalLog.CLAIM,
            notes = notes
        )
        self.save(post_save=True)

        return generate_success_response(
            status_str=AVAILABLE_STATUSES[self.status][1],
            data={
                "uuid": self.uuid,
                "status": AVAILABLE_STATUSES[self.status][0]
            }
        )


    @is_status([IN_REVIEW_CODE, IN_ADMIN_REVIEW_CODE])
    def unclaim(self, user, notes=''):
        """Unclaims a change object for review or admin review for the given user 
        and updates the log. Will move the change back to the previous approval step.

        Args:
            user (User): User unclaiming the object for review or admin review
            notes (str, optional): Notes field. Defaults to ''.

        Returns:
            [dict]: {"success", "message", "data": {"uuid", "status"}}
        """

        # check if unclaiming user is the same as the claiming user or if unclaiming user is admin
        latest_log = self.get_latest_log()
        if user.get_role_display() != ADMIN:
            if latest_log.user != user:
                return generate_failure_response(
                    "To unclaim an item the user must be the same as the claiming user, or must be admin."
                )

        self._goto_previous_approval_stage()

        ApprovalLog.objects.create(
            change = self,
            user = user,
            action = ApprovalLog.UNCLAIM,
            notes = notes
        )
        self.save(post_save=True)

        return generate_success_response(
            status_str=AVAILABLE_STATUSES[self.status][1],
            data={
                "uuid": self.uuid,
                "status": AVAILABLE_STATUSES[self.status][0]
            }
        )

    def _add_create_edit_approval_log(self):
        """
            Adds a CREATE or EDIT approval log to the change object
            based on conditions
        """

        # change object was freshly created and has no logs
        if not ApprovalLog.objects.filter(change=self).exists():
            ApprovalLog.objects.create(
                change=self,
                user=get_current_user(),
                action=ApprovalLog.CREATE,
            )

        elif self.status in [CREATED_CODE, IN_PROGRESS_CODE]:
            # don't create an EDIT ApprovalLog for a rejection, claim, or unclaim
            if self.get_latest_log().action not in [ApprovalLog.REJECT, ApprovalLog.CLAIM, ApprovalLog.UNCLAIM]:
                ApprovalLog.objects.create(
                    change=self,
                    user=get_current_user(),
                    action=ApprovalLog.EDIT,
                )


# create approval logs after the Change model is saved
@receiver(post_save, sender=Change, dispatch_uid="save")
def create_approval_log_dispatcher(sender, instance, **kwargs):
    instance._add_create_edit_approval_log()
