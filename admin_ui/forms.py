from django import forms
from django.core.exceptions import ValidationError

from api_app.models import (
    Change,
    AVAILABLE_STATUSES,
    CREATED_CODE,
    IN_REVIEW_CODE,
    IN_ADMIN_REVIEW_CODE,
    IN_PROGRESS_CODE,
    AWAITING_REVIEW_CODE,
    AWAITING_ADMIN_REVIEW_CODE,
)
from admg_webapp.users.models import User, ADMIN_CODE


class TransitionForm(forms.Form):
    change = forms.ModelChoiceField(queryset=Change.objects.all())
    notes = forms.Textarea()
    transition = forms.ChoiceField(choices=())

    def __init__(self, *args, valid_transitions, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["transition"].choices = valid_transitions

    def transition_change(self, user):
        change = self.cleaned_data["change"]
        func = getattr(change, self.cleaned_data["action"])
        # TODO

    def get_supported_actions(self, change: Change, user: User):
        actions = set()

        if change.status in [CREATED_CODE, IN_PROGRESS_CODE]:
            actions.add("submit", "Ready for Staff Review")

        if change.status in [IN_REVIEW_CODE]:
            actions.add(("review", "Ready for Admin Review"))

        if change.status in [IN_REVIEW_CODE, IN_ADMIN_REVIEW_CODE]:
            actions.add(("reject", "Requires adjustments"))

        if change.status in [AWAITING_REVIEW_CODE, AWAITING_ADMIN_REVIEW_CODE]:
            next_approver = (
                "Staff" if change.status == AWAITING_REVIEW_CODE else "Admin"
            )
            actions.add(("claim", f"Claim for {next_approver} Review"))

        if change.status in [IN_REVIEW_CODE, IN_ADMIN_REVIEW_CODE]:
            actions.add(("unclaim", "Unassign Reviewer"))

        if user.role == ADMIN_CODE:
            # TODO: Rework so that admin is prompted to verify if change.status != IN_ADMIN_REVIEW_CODE
            actions.add(
                ("publish", "Publish to production")
            )  # Admin can publish at any step

        return actions

    # def check_for_error(self, response):
    #     if response["success"]:
    #         messages.success(self.request, "Status successfully changed.")
    #     else:
    #         messages.error(self.request, response["message"])
