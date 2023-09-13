import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe


@login_required
@user_passes_test(lambda user: user.is_admg_admin())
def trigger_deploy(request):
    try:
        workflow = settings.GITHUB_WORKFLOW
    except AttributeError:
        messages.add_message(
            request,
            messages.ERROR,
            "Failed to trigger deployment: Github workflow not specified in settings.",
        )
        return HttpResponseRedirect(reverse("summary"))

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
                f'<a href="https://github.com/{workflow["repo"]}/actions/workflows/{workflow["id"]}" target="_blank">here</a>.'
            ),
        )
    else:
        messages.add_message(
            request, messages.ERROR, f"Failed to trigger deployment: {response.text}"
        )

    return HttpResponseRedirect(reverse("summary"))
