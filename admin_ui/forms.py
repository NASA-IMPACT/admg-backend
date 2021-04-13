from collections import OrderedDict

from django import forms
from django.core.exceptions import ValidationError
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from crispy_forms.helper import FormHelper

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
from data_models import models as data_models
from .widgets import IconBoolean


class TransitionForm(forms.Form):
    """
    Form to assist in transitioning a Change model through the approval process.
    Must be initialized with a user and change object, both of which are used when
    determining what are valid transitions based on the change's current status and
    the user's permissions.
    """

    transition = forms.ChoiceField(
        required=True,
        choices=(),
        widget=forms.RadioSelect(),
        help_text="Alter this draft's approval status.",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 5}),
        help_text="Notes for other team members.",
    )

    def __init__(self, *args, change: Change, user: User, **kwargs):
        super().__init__(*args, **kwargs)
        self.change = change
        self.user = user
        self.fields["transition"].choices = self.get_supported_actions(change, user)

    def apply_transition(self):
        transition_func = getattr(self.change, self.cleaned_data["transition"])
        return transition_func(self.user, self.cleaned_data["notes"])

    @staticmethod
    def get_supported_actions(change: Change, user: User):
        actions = OrderedDict()

        if change.status in [CREATED_CODE, IN_PROGRESS_CODE]:
            actions["submit"] = "Ready for Staff Review"

        if change.status in [AWAITING_REVIEW_CODE]:
            actions["claim"] = "Claim for Staff Review"

        if change.status in [IN_REVIEW_CODE]:
            actions["reject"] = "Requires adjustments"

        if change.status in [IN_REVIEW_CODE]:
            actions["unclaim"] = "Unassign Staff Reviewer"

        if change.status in [IN_REVIEW_CODE]:
            actions["review"] = "Ready for Admin Review"

        if user.role == ADMIN_CODE:
            if change.status in [IN_ADMIN_REVIEW_CODE]:
                actions["reject"] = "Requires adjustments"

            if change.status in [AWAITING_ADMIN_REVIEW_CODE]:
                actions["claim"] = "Claim for Admin Review"

            # Admin can publish at any step
            actions["publish"] = "Publish to production"
            if change.status != IN_ADMIN_REVIEW_CODE:
                actions["publish"] = mark_safe(
                    '<span class="text-danger font-italic">Danger:</span>  '
                    + actions["publish"]
                )

        return actions.items()


class DoiForm(forms.ModelForm):
    keep = forms.BooleanField(initial=True, widget=IconBoolean)
    # TODO:
    # - FK fields should show Drafts, not just published data
    # - If a DOI does not have a DOI field, render the Concept ID with a link to EarthdataSearch
    # - Allow a user to edit DOI if no value is provided?
    class Meta:
        model = data_models.DOI
        fields = [
            "campaigns",
            "instruments",
            "platforms",
            "collection_periods",
            "keep",
        ]

    def __init__(self, *args, choices, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, choices in choices.items():
            self.fields[field_name].choices = choices


class DoiFormSet(forms.formset_factory(DoiForm, extra=0)):
    @cached_property
    def choices(self):
        # To avoid redundant queries for the M2M fields within each of this
        # formset's forms, we manually build the choices outside of the form.
        # https://code.djangoproject.com/ticket/22841
        return {
            "campaigns": list(
                forms.ModelChoiceField(data_models.Campaign.objects.all()).choices
            ),
            "instruments": list(
                forms.ModelChoiceField(data_models.Instrument.objects.all()).choices
            ),
            "platforms": list(
                forms.ModelChoiceField(data_models.Platform.objects.all()).choices
            ),
            "collection_periods": list(
                forms.ModelChoiceField(
                    data_models.CollectionPeriod.objects.all().select_related(
                        "deployment__campaign", "platform"
                    )
                ).choices
            ),
        }

    def get_form_kwargs(self, index):
        return {
            **super().get_form_kwargs(index),
            "choices": self.choices,
        }


class TableInlineFormSetHelper(FormHelper):
    template = "bootstrap/table_inline_formset.html"
