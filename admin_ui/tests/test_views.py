from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse


from data_models.models import Campaign
from api_app.models import CREATE

from . import factories


class TestChangeUpdateView(TestCase):
    def setUp(self):
        self.change = factories.ChangeFactory.create(
            content_type=ContentType.objects.get_for_model(Campaign),
            action=CREATE
        )
        self.user = factories.UserFactor.create()
        self.url = reverse("change-update", args=(self.change.uuid,))

    def test_requires_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"{reverse('account_login')}?next={self.url}", response.url)