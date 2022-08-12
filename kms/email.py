import boto3
from django.template.loader import get_template
from premailer import transform
from typing import List, Optional

client = boto3.client("ses")


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
    return client.send_email(
        Destination={"ToAddresses": recipients},
        Message={
            "Body": {"Html": {"Data": template.html}, "Text": {"Data": template.text}},
            "Subject": {"Data": template.subject},
        },
        # TODO: Set this as the ADMG admin email
        Source="john@developmentseed.org",
    )
