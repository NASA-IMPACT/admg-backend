from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
from django.forms import ModelForm, Textarea, modelform_factory
from django.utils.safestring import mark_safe
# from django.views.generic.detail import DetailView
# from django.views.generic.edit import ModelFormMixin
from django.views.generic.edit import UpdateView

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


class ChangeForm(ModelForm):
    class Meta:
        model = Change
        exclude = []
        widgets = {
            'notes': Textarea()
        }


class CampaignGroupView(UpdateView):
    template_name = "admin/change_group_detail.html"
    pk_url_kwarg = "uuid"

    def get_queryset(self):
        return Change.objects.filter(
            content_type__model__iexact="campaign",
            action="Create"  # Limit to only Create changes for now
        )

    def get_form_class(self):
        # https://github.com/django/django/blob/354c1524b38c9b9f052c1d78dcbfa6ed5559aeb3/django/contrib/admin/options.py#L670-L711
        # https://github.com/django/django/blob/354c1524b38c9b9f052c1d78dcbfa6ed5559aeb3/django/forms/models.py#L483
        # return modelform_factory(self.object.__class__)
        return modelform_factory(self.object.content_type.model_class(), exclude=[])

    def get_initial(self):
        return self.object.update

    def get_context_data(self):
        return {
            **super().get_context_data(),
            'change_form': ChangeForm(instance=self.object, prefix='change__')
        }
