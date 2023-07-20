from typing import List, Optional

from django.conf import settings
from django.core import mail
from django.template.loader import get_template
from premailer import transform


class Template:
    def __init__(
        self,
        html_template_name: str,
        text_template_name: str,
        subject: str,
        props: Optional[dict] = None,
    ):
        self.html_template_name = html_template_name
        self.text_template_name = text_template_name
        self.subject = subject
        self.props = props or {}

    def render(self, template_name: str, premailer_transform: bool = False):
        t = get_template(template_name).render(self.props)
        return transform(t) if premailer_transform else t

    @property
    def text(self):
        return self.render(self.text_template_name).strip()

    @property
    def html(self):
        return self.render(self.html_template_name, True)


def gcmd_changes_email(template: Template, recipients: List[str]):
    with mail.get_connection() as connection:
        mail.send_mail(
            template.subject,
            message=template.text,
            html_message=template.html,
            from_email=settings.GCMD_SYNC_SOURCE_EMAIL,
            recipient_list=recipients,
            connection=connection,
        )
