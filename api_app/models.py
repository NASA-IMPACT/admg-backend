from datetime import date, datetime
from uuid import UUID, uuid4

from admg_webapp.users.models import User
from crum import get_current_user
from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Subquery, aggregates, expressions, functions
from django.db.models.fields.json import KeyTextTransform
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from admg_webapp.users.models import ADMIN, User
from data_models import serializers


def generate_failure_response(message):
    return {"success": False, "message": message}


def generate_success_response(status_str, data):
    return {
        "success": True,
        "message": f"Change object has been moved to the '{status_str}' stage.",
        "data": data,
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

    if user.get_role_display() != User.Roles.ADMIN.label:
        return generate_failure_response("action failed because initiating user was not admin")


def is_admin(function):
    def wrapper(self, user, notes="", **kwargs):

        if not_admin := is_not_admin(user):
            if not kwargs.get("doi"):
                return not_admin

        result = function(self, user, notes)

        return result

    return wrapper


def is_status(accepted_statuses_list):
    def decorator(function):
        def wrapper(self, user, notes=""):

            if self.status not in accepted_statuses_list:
                status_strings = [status.label for status in accepted_statuses_list]
                return generate_failure_response(
                    f"action failed because status was not one of {status_strings}"
                )

            result = function(self, user, notes)

            return result

        return wrapper

    return decorator


class ApprovalLog(models.Model):
    """Keeps a log of the changes (publish, reject, etc) made to a particular draft"""

    class Actions(models.IntegerChoices):
        TRASH = -1, "trash"
        UNTRASH = 0, "untrash"
        CREATE = 1, "create"
        EDIT = 2, "edit"
        SUBMIT = 3, "submit"
        REVIEW = 4, "review"
        PUBLISH = 5, "publish"
        REJECT = 6, "reject"
        CLAIM = 7, "claim"
        UNCLAIM = 8, "unclaim"

    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    change = models.ForeignKey("Change", on_delete=models.CASCADE, blank=True)

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="user", null=True, blank=True
    )

    date = models.DateTimeField(auto_now_add=True)

    action = models.IntegerField(choices=Actions.choices, default=Actions.CREATE)
    notes = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.user} | {self.get_action_display()} | {self.notes} | {self.date}"

    class Meta:
        ordering = ["-date"]

    def get_action_display_past_tense(self):
        action = self.get_action_display()
        return f"{action}d" if action.endswith("e") else f"{action}ed"


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
                queryset=ApprovalLog.objects.order_by(order_by).select_related(*select_related),
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
                        action=Change.Actions.CREATE,
                        uuid=expressions.OuterRef(uuid_dest_attr),
                    )
                    .values(f"update__{identifier}")[:1]
                ),
            }
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
                        (of_type.objects.filter(uuid=expressions.OuterRef("uuid"))[:1]).values(
                            identifier
                        )
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
        FIELD_UNVIEWED: "unviewed",
        FIELD_INCORRECT: "incorrect",
        FIELD_UNSURE: "unsure",
        FIELD_CORRECT: "correct",
    }

    class Statuses(models.IntegerChoices):
        # The change has been freshly ingested, but no one has made edits using the admin interface
        CREATED = 0, "Created"
        # The change is in progress, can not be approved, but the user can update the change request
        IN_PROGRESS = 1, "In Progress"
        # The change has been added to the review pile, but hasn't been claimed
        AWAITING_REVIEW = 2, "Awaiting Review"
        # The change as been claimed, and can now be can now be reviewed or rejected. Rejection sends it back to the in_progress state
        IN_REVIEW = 3, "In Review"
        # The change has been added to the admin review pile, but hasn't been claimed
        AWAITING_ADMIN_REVIEW = 4, "Awaiting Admin Review"
        # Can be published or rejected. Rejection sends it back to the in_progress state
        IN_ADMIN_REVIEW = 5, "In Admin Review"
        # Once approved the changes in the change table is refected to the model
        # The state of the change object can not be changed from this state.
        PUBLISHED = 6, "Published"
        # The change has been moved to the trash
        IN_TRASH = 7, "In Trash"

    class Actions(models.TextChoices):
        CREATE = "Create"
        UPDATE = "Update"
        DELETE = "Delete"

    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    content_type = models.ForeignKey(
        ContentType,
        help_text="Model for which the draft pertains.",
        on_delete=models.CASCADE,
    )
    model_instance_uuid = models.UUIDField(default=uuid4, blank=True, null=True)
    content_object = GenericForeignKey("content_type", "model_instance_uuid")

    status = models.IntegerField(choices=Statuses.choices, default=Statuses.IN_PROGRESS)
    update = models.JSONField(default=dict, blank=True)
    field_status_tracking = models.JSONField(default=dict, blank=True)
    previous = models.JSONField(default=dict)

    action = models.CharField(
        max_length=10,
        choices=((choice, choice) for choice in Actions),
        default=Actions.UPDATE,
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
            raise KeyError("The field_status provided is not among the built statuses") from E

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
            field.name: {"status": self.FIELD_DEFAULT, "notes": ""}
            for field in source_model._meta.fields
        }

    @property
    def model_name(self):
        # TODO: Verify that this works with API
        cls = self.content_type.model_class()
        return cls.__name__ if cls else "UNKNOWN"

    @property
    def is_locked(self):
        """
        Helper to specify when an object should be locked (ie no longer can be edited)
        """
        return self.status in [self.Statuses.PUBLISHED, self.Statuses.IN_TRASH]

    def __str__(self):
        return f"{self.model_name} >> {self.uuid}"

    @classmethod
    def _get_processed_value(cls, value):
        """
        Serialize field values for storage in JSONField columns.
        """
        if isinstance(value, UUID):
            return str(value)
        elif isinstance(value, list):
            return [cls._get_processed_value(val) for val in value]
        elif isinstance(value, date) or isinstance(value, datetime):
            return value.isoformat()

        return value

    def _check_model_and_uuid(self):
        """
        The method will raise loud errors if the model doesn't exist
        or the uuid deosn't exist in case of edit/delete change
        """
        model = apps.get_model("data_models", self.model_name)
        if self.action != Change.Actions.CREATE:
            serializer_class = getattr(serializers, f"{self.model_name}Serializer")
            instance = model.objects.get(uuid=self.model_instance_uuid)
            if self.action == Change.Actions.UPDATE:
                serializer = serializer_class(instance)
                self.previous = {
                    key: Change._get_processed_value(serializer.data.get(key))
                    for key in self.update
                }

    def get_latest_log(self):
        return ApprovalLog.objects.filter(change=self).order_by("date").last()

    def get_ancestors(self):
        """
        Get record and all ancestry records.
        """
        # We use a recursive CTE to allow us to get all of the UUIDs of
        # this change and all of its ancestors. We join the data to the
        # django_content_type table to allow us to customize how the
        # relationship between parent and child is linked (ie on which
        # field). UUIDs come out in order of this change first, then its
        # parent, parent's parent, and so on.
        query = f"""
            WITH RECURSIVE parent AS (
                SELECT
                    c.uuid,
                    c.update,
                    ct.model
                FROM
                    {self._meta.db_table} c,
                    django_content_type ct
                WHERE
                    c.content_type_id = ct.id
                    AND c.uuid = %s
                UNION ALL
                SELECT
                    c.uuid,
                    c.update,
                    ct.model
                FROM
                    {self._meta.db_table} c,
                    django_content_type ct,
                    parent p
                WHERE
                    c.content_type_id = ct.id
                    -- The only time we want campaign relationships is when
                    -- looking up the parent of a deployment
                    AND CASE WHEN p.model ~* 'deployment|doi' THEN
                        p.update ->> 'campaign' = c.uuid::text
                    ELSE
                        p.update ->> 'deployment' = c.uuid::text
                    END
            )
            SELECT
                uuid::text
            FROM
                parent
        """
        uuids = [c.uuid for c in Change.objects.raw(query, [self.uuid])]
        # Using this "uuid__in" trick allows us to return a standard queryset
        # rather than a RawQueryset. This means we can use all of the other
        # queryset helpers like ".select_related()". However, this can return records
        # out of order so we also need to reinforce the order by adding a "place"
        # attribute on each record.
        return (
            Change.objects.filter(uuid__in=uuids).annotate(
                place=expressions.RawSQL("select array_position(%s, uuid::text)", [uuids])
            )
            # Reverse the order so that this change is last in list
            .order_by("-place")
        )

    def get_descendents(self):
        return self.__class__.objects.filter(
            **{f"update__{self.content_type.model}": str(self.uuid)},
            # Hack: Some draft IOPs, SigEvents, and CollectionPeriods will have a 'update.campaign'
            # property, despite the fact that the actual models do not store that detail. We want to
            # ignore those records as they misrepresent the heirarchy of the data.
            **({"content_type__model": "deployment"} if self.model_name == "Campaign" else {}),
        )

    def check_prior_unpublished_update_exists(self):
        """This checks to see there is an existing Update draft which has not yet been published
        and links to the same data_model as the current proposed draft. The intention is to allow
        a check to prevent two simultaneous update drafts

        Returns:
            bool: True if there is existing update draft
        """
        if self.action == self.Actions.UPDATE:
            return bool(
                Change.objects.filter(model_instance_uuid=self.model_instance_uuid)
                .exclude(status=self.Statuses.PUBLISHED)
                .exclude(uuid=self.uuid)
            )
        return False

    def save(self, *args, post_save=False, **kwargs):
        # do not check for validity of model_name and uuid if it has been approved or rejected.
        # Check is done for the first time only
        # post_save=False prevents self.previous from being set
        if not post_save:
            self._check_model_and_uuid()

        # change object was freshly created and has no logs
        if not ApprovalLog.objects.filter(change=self).exists():
            self.status = self.Statuses.CREATED
            # the post_save function handles the creation of the approval log
        # should only log changes made to the draft while in progress
        elif self.status == self.Statuses.CREATED:
            self.status = self.Statuses.IN_PROGRESS

        if not self.field_status_tracking:
            self.generate_field_status_tracking_dict()

        if self.check_prior_unpublished_update_exists():
            raise ValidationError(
                {"model_instance_uuid": "Unpublished draft already exists for this model uuid."}
            )

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

        return "All serializer validations passed"

    def validate(self):
        """Runs the serializer validation. Note that different request types will
        have partial or non-partial validation. If errors are found, the error
        handler will capture them and this function's return will be bypassed.

        Returns:
            Response: Returns a 200 with a validation message, only if the valdations
            pass. Otherwise, the error handler will print out each validation error string
            and error code.
        """
        if self.action == Change.Actions.CREATE:
            validation_message = self._run_validator(partial=False)

        elif self.action == Change.Actions.UPDATE:
            validation_message = self._run_validator(partial=True)

        elif self.action == Change.Actions.DELETE:
            validation_message = ""

        return Response(status=200, data={"message": validation_message})

    def _get_model_instance(self):
        model = apps.get_model("data_models", self.model_name)
        return model.objects.get(uuid=self.model_instance_uuid)

    def _save_serializer(self, model_instance, data, partial):
        serializer_class = getattr(serializers, f"{self.model_name}Serializer")
        serializer = serializer_class(instance=model_instance, data=data, partial=partial)

        if serializer.is_valid(raise_exception=True):
            new_model_instance = serializer.save()
            return {"uuid": new_model_instance.uuid, "status": self.Statuses.PUBLISHED}

    def _create(self):
        # set the db uuid == change request uuid
        self.update["uuid"] = str(self.uuid)

        return self._save_serializer(model_instance=None, data=self.update, partial=False)

    def _update(self):
        model_instance = self._get_model_instance()
        if not self.model_instance_uuid:
            raise ValidationError({"uuid": "UUID for the model was not found"})

        return self._save_serializer(model_instance=model_instance, data=self.update, partial=True)

    def _delete(self):
        model_instance = self._get_model_instance()
        if not self.model_instance_uuid:
            raise serializers.ValidationError({"uuid": "UUID for the model was not found"})

        self.update = {
            key: Change._get_processed_value(getattr(model_instance, key))
            for key in model_instance.__dict__
            if not key.startswith("_")
        }
        self.save(post_save=True)
        model_instance.delete()

        return {"uuid": self.model_instance_uuid, "status": self.Statuses.PUBLISHED}

    @is_status([Statuses.CREATED, Statuses.IN_PROGRESS])
    def submit(self, user, notes=""):
        self.status = self.Statuses.AWAITING_REVIEW

        ApprovalLog.objects.create(
            change=self, user=user, action=ApprovalLog.Actions.SUBMIT, notes=notes
        )

        self.save(post_save=True)

        return generate_success_response(
            status_str=self.Statuses.AWAITING_REVIEW.label,
            data={"uuid": self.uuid, "status": self.Statuses.AWAITING_REVIEW},
        )

    @is_status([Statuses.IN_REVIEW])
    def review(self, user, notes=""):
        self.status = self.Statuses.AWAITING_ADMIN_REVIEW
        ApprovalLog.objects.create(
            change=self, user=user, action=ApprovalLog.Actions.REVIEW, notes=notes
        )
        self.save(post_save=True)

        return generate_success_response(
            status_str=self.Statuses.AWAITING_ADMIN_REVIEW.label,
            data={"uuid": self.uuid, "status": self.Statuses.AWAITING_ADMIN_REVIEW},
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

        if self.action == Change.Actions.CREATE:
            response = self._create()
        elif self.action == Change.Actions.UPDATE:
            response = self._update()
        elif self.action == Change.Actions.DELETE:
            response = self._delete()

        # links co to the new db instance
        # this is not what syncs the UUIDs
        if self.action == Change.Actions.CREATE:
            self.model_instance_uuid = response["uuid"]

        if self.status != self.Statuses.IN_ADMIN_REVIEW:
            ApprovalLog.objects.create(
                change=self,
                user=admin_user,
                action=ApprovalLog.Actions.REVIEW,
                notes=notes,
            )

        ApprovalLog.objects.create(
            change=self,
            user=admin_user,
            action=ApprovalLog.Actions.PUBLISH,
            notes=notes,
        )

        self.status = self.Statuses.PUBLISHED

        self.save(post_save=True)

        return generate_success_response(
            status_str=self.Statuses.PUBLISHED.label,
            data={
                "updated_model": self.model_name,
                "action": self.action,
                "uuid_changed": response["uuid"],
                "status": self.Statuses.PUBLISHED,
            },
        )

    @is_admin
    @is_status(
        [
            Statuses.CREATED,
            Statuses.IN_PROGRESS,
            Statuses.AWAITING_REVIEW,
            Statuses.IN_REVIEW,
            Statuses.AWAITING_ADMIN_REVIEW,
            Statuses.IN_ADMIN_REVIEW,
        ]
    )
    def trash(self, user, notes="", doi=False):
        """Moves a change object to the IN_TRASH stage. Expected use case
        is for DOIs which need to be ignored and items created accidently.
        Items can be removed from the trash with self.untrash()

        Args:
            user (User): User trashing the object
            notes (string): Extra notes that were provided by the trashing user. Default is ''.

        Returns:
            [dict]: {"success", "message", "data": {"uuid", "status"}}
        """

        self.status = self.Statuses.IN_TRASH
        ApprovalLog.objects.create(
            change=self, user=user, action=ApprovalLog.Actions.TRASH, notes=notes
        )
        self.save(post_save=True)

        return generate_success_response(
            status_str=self.Statuses.IN_TRASH.label,
            data={"uuid": self.uuid, "status": self.Statuses.IN_TRASH},
        )

    @is_admin
    @is_status([Statuses.IN_TRASH])
    def untrash(self, user, notes="", doi=False):
        """Moves a change object from trash to the in progress stage.

        Args:
            user (User): User untrashing the object
            notes (string): Extra notes that were provided by the untrashing user. Default is ''.

        Returns:
            [dict]: {"success", "message", "data": {"uuid", "status"}}
        """

        self.status = self.Statuses.IN_PROGRESS
        ApprovalLog.objects.create(
            change=self, user=user, action=ApprovalLog.Actions.UNTRASH, notes=notes
        )
        self.save(post_save=True)

        return generate_success_response(
            status_str=self.Statuses.IN_PROGRESS.label,
            data={"uuid": self.uuid, "status": self.Statuses.IN_PROGRESS},
        )

    @is_status([Statuses.IN_REVIEW, Statuses.IN_ADMIN_REVIEW])
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

        self.status = self.Statuses.IN_PROGRESS
        ApprovalLog.objects.create(
            change=self, user=user, action=ApprovalLog.Actions.REJECT, notes=notes
        )
        self.save(post_save=True)

        return generate_success_response(
            status_str=self.Statuses.IN_PROGRESS.label,
            data={"uuid": self.uuid, "status": self.Statuses.IN_PROGRESS},
        )

    def _goto_next_approval_stage(self):
        """Do not call this, it is an internal function"""
        self.status += 1

    def _goto_previous_approval_stage(self):
        """Do not call this, it is an internal function"""
        self.status -= 1

    @is_status([Statuses.AWAITING_REVIEW, Statuses.AWAITING_ADMIN_REVIEW])
    def claim(self, user, notes=""):
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
        if self.status == self.Statuses.AWAITING_ADMIN_REVIEW:
            if not_admin := is_not_admin(user):
                return not_admin

        self._goto_next_approval_stage()

        ApprovalLog.objects.create(
            change=self, user=user, action=ApprovalLog.Actions.CLAIM, notes=notes
        )
        self.save(post_save=True)

        return generate_success_response(
            status_str=next(status.label for status in Change.Statuses if status == self.status),
            data={"uuid": self.uuid, "status": self.status},
        )

    @is_status([Statuses.IN_REVIEW, Statuses.IN_ADMIN_REVIEW])
    def unclaim(self, user, notes=""):
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
        if user.get_role_display() != User.Roles.ADMIN.label:
            if latest_log.user != user:
                return generate_failure_response(
                    "To unclaim an item the user must be the same as the claiming user,"
                    " or must be admin."
                )

        self._goto_previous_approval_stage()

        ApprovalLog.objects.create(
            change=self, user=user, action=ApprovalLog.Actions.UNCLAIM, notes=notes
        )
        self.save(post_save=True)

        return generate_success_response(
            status_str=next(status.label for status in Change.Statuses if status == self.status),
            data={"uuid": self.uuid, "status": self.status},
        )

    def _add_create_edit_approval_log(self):
        """
        Adds a Change.Actions.CREATE or EDIT approval log to the change object
        based on conditions
        """

        # change object was freshly created and has no logs
        if not ApprovalLog.objects.filter(change=self).exists():
            ApprovalLog.objects.create(
                change=self, user=get_current_user(), action=ApprovalLog.Actions.CREATE
            )

        elif self.status in [self.Statuses.CREATED, self.Statuses.IN_PROGRESS]:
            # don't create an EDIT ApprovalLog for a rejection, claim, or unclaim
            if self.get_latest_log().action not in [
                ApprovalLog.Actions.REJECT,
                ApprovalLog.Actions.CLAIM,
                ApprovalLog.Actions.UNCLAIM,
            ]:
                ApprovalLog.objects.create(
                    change=self,
                    user=get_current_user(),
                    action=ApprovalLog.Actions.EDIT,
                )


# create approval logs after the Change model is saved
@receiver(post_save, sender=Change, dispatch_uid="save")
def create_approval_log_dispatcher(sender, instance, **kwargs):
    instance._add_create_edit_approval_log()


class Recommendation(models.Model):
    change = models.ForeignKey(Change, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True)
    object_uuid = models.UUIDField()
    casei_object = GenericForeignKey("content_type", "object_uuid")
    result = models.BooleanField(verbose_name="Was the CASEI object connected?", null=True)
    submitted = models.BooleanField(
        verbose_name="Has the user published their result?", blank=False, default=False
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["change", "object_uuid"], name="unique_recommendation")
        ]

    def __str__(self):
        return f"{self.id} >> {self.change} >> {self.casei_object}"


class SubqueryCount(Subquery):
    template = "(SELECT count(*) FROM (%(subquery)s) _count)"
    output_field = models.IntegerField()
