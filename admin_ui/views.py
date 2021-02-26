import json

from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import models
from django.forms import modelform_factory
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.db.models.query import QuerySet
from rest_framework.renderers import JSONRenderer
import requests

from api_app.models import Change, CREATE, UPDATE


@login_required
@user_passes_test(lambda user: user.can_deploy())
def deploy_admin(request):
    workflow = settings.GITHUB_WORKFLOW

    response = requests.post(
        url=f"https://api.github.com/repos/{workflow['repo']}/actions/workflows/{workflow['id']}/dispatches",
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {workflow['token']}",
        },
        json={"ref": workflow["branch"]},
    )
    if response.ok:
        messages.add_message(
            request,
            messages.INFO,
            mark_safe(
                "Successfully triggered deployment. See details "
                f'<a href="https://github.com/{workflow["repo"]}/actions?query=workflow%3ADeploy" target="_blank">here</a>.'
            ),
        )
    else:
        messages.add_message(
            request, messages.ERROR, f"Failed to trigger deployment: {response.text}"
        )

    # TODO: Redirect back to origin of request
    # TODO: Use dynamic admin route (either from URL router or from settings)
    return HttpResponseRedirect("/admin/")


class ChangeCreateView(CreateView):
    model = Change
    fields = [
        "content_type",
        "model_instance_uuid",
        "action",
        "update",
    ]
    template_name_suffix = '_add_form'

    def get_initial(self):
        # TODO: given self.request.GET.get('parent'), determine correct initial data for each content_type
        return {
            'content_type': ContentType.objects.get(app_label='data_models', model__iexact=self.kwargs['model']).id,
            'action': UPDATE if self.request.GET.get('uuid') else CREATE,
            'model_instance_uuid': self.request.GET.get('uuid')
        }

    # TODO: Render destination model form


class ChangeDetailView(DetailView):
    model = Change


class ChangeUpdateView(UpdateView):
    success_url = "/"
    fields = [
        "content_type",
        "model_instance_uuid",
        "action",
        "update",
        "status",
    ]

    prefix = "change"
    destination_model_prefix = "model_form"

    def get_queryset(self):
        # Prefetch content type for performance
        return Change.objects.select_related("content_type")

    @property
    def destination_model_form(self):
        """ Helper to return a form for the destination of the Draft object """
        return modelform_factory(
            self.get_object().content_type.model_class(), exclude=[]
        )

    def get_context_data(self, **kwargs):
        if "model_form" not in kwargs:
            kwargs["model_form"] = self.destination_model_form(
                initial=self.get_object().update, prefix=self.destination_model_prefix
            )
        return {
            **super().get_context_data(**kwargs),
            # Add approvals to context
            "approvals": self.get_object().approvallog_set.order_by("-date"),
        }

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = self.get_object()

        # Validate destination model's form
        class ModelForm(self.destination_model_form):
            def validate_unique(_self):
                # We don't want to raise errors on unique errors for the
                # destination model unless this is a "Create" change
                if self.object.action == CREATE:
                    super().validate_unique()

        model_form = ModelForm(data=request.POST, prefix=self.destination_model_prefix)
        form = self.get_form()

        if not all([model_form.is_valid(), form.is_valid()]):
            return self.form_invalid(form=form, model_form=model_form)

        # Populate Change's form with values from destination model's form
        form.instance.update = json.loads(
            JSONRenderer().render(
                {k: serialize(v) for k, v in model_form.cleaned_data.items()}
            )
        )
        return self.form_valid(form)

    def form_invalid(self, form, model_form):
        # Overriden to support handling both invalid Change form and an invalid
        # destination model form
        return self.render_to_response(
            self.get_context_data(form=form, model_form=model_form)
        )


def serialize(value):
    if isinstance(value, QuerySet):
        return [v.uuid for v in value]
    if isinstance(value, models.Model):
        return value.uuid
    return value
