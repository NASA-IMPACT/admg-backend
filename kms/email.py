from typing import List, Optional

from django.conf import settings
from django.core import mail
from django.template.loader import get_template
from premailer import transform


class Template:
    def __init__(self, template_name: str, subject: str, props: Optional[dict] = None):
        self.template_name = template_name
        self.subject = subject
        self.props = props or {}

    def render(self, extension: str):
        return transform(get_template(self.template_name).render(self.props))

    @property
    def text(self):
        return self.render("txt")

    @property
    def html(self):
        return self.render("html")


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
