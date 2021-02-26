from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import modelform_factory
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.views.generic.edit import UpdateView
from django.views import View
from django.shortcuts import render
from django.forms import ModelForm

import requests

from api_app.models import Change


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


class CampaignGroupView(UpdateView):
    pk_url_kwarg = "uuid"
    success_url = "/"
    fields = ["action", "content_type"]

    prefix = "change"
    destination_model_prefix = "model_form"

    def get_queryset(self):
        # Prefetch content type for performance
        return Change.objects.select_related("content_type")

    # def get_form_class(self):
    #     # We want to render this with a form for the Change's destination model,
    #     # not for the Change model.
    #     return modelform_factory(self.object.content_type.model_class(), exclude=[])

    # def get_initial(self):
    #     # Populate form with Update object
    #     return self.object.update

    @property
    def destination_model_form(self):
        """ Helper to return a form for the destination of the Draft object """
        return modelform_factory(
            self.get_object().content_type.model_class(), exclude=[]
        )

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            # Add approvals to context
            "model_form": self.destination_model_form(
                initial=self.get_object().update, prefix=self.destination_model_prefix
            ),
            "approvals": self.get_object().approvallog_set.order_by("-date"),
        }

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """

        # Validate destination model's form
        class ModelForm(self.destination_model_form):
            def validate_unique(self):
                # https://stackoverflow.com/a/4112531/728583
                pass

        destination_model_form = ModelForm(
            data=request.POST, prefix=self.destination_model_prefix
        )
        if not destination_model_form.is_valid():
            return self.form_invalid(destination_model_form)

        # Validate current model
        form = self.get_form()
        if not form.is_valid():
            return self.form_invalid(form)

        form.instance.update = {
            k: v
            for k, v in destination_model_form.data.dict().items()
            if k != "csrfmiddlewaretoken"
        }
        return self.form_valid(form)

    # def form_invalid(self, form):
    #     print("bad")
    #     return super().form_invalid(form)

    # def form_valid(self, form):
    #     if form.is_valid():
    #         ChangeForm = modelform_factory(Change, exclude=[])
    #         change_form = ChangeForm(
    #             {
    #                 k: v
    #                 for k, v in form.data.dict().items()
    #                 if k != "csrfmiddlewaretoken"
    #             }
    #         )
    #         if change_form.is_valid():
    #             return super().form_valid(form)
    #     return super().form_valid(form)


class ChangeForm(ModelForm):
    class Meta:
        model = Change
        fields = [
            "action",
            "status",
            # "uuid",
            "model_instance_uuid",
            "content_type",
            "model_instance_uuid",
            "status",
            "update",
        ]


class MyFormView(View):
    change_form_class = ChangeForm
    initial = {"key": "value"}
    template_name = "form_template.html"

    @property
    def model_form_class(self):
        """ Helper to return a form for the destination of the Draft object """
        base_model_form = modelform_factory(
            self.get_object().content_type.model_class(), exclude=[]
        )

        class ModelFormCls(base_model_form):
            ...

        return ModelFormCls

    def get(self, request, *args, **kwargs):
        form = self.change_form_class(initial=self.initial)
        model_form = self.model_form_class(initial=)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            # <process form cleaned data>
            return HttpResponseRedirect("/success/")

        return render(request, self.template_name, {"form": form})
