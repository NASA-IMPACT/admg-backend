from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from data_models.models import Campaign, Season
from api_app.models import Change

from . import factories


class TestChangeUpdateView(TestCase):
    def setUp(self):
        self.change = factories.ChangeFactory.create(
            content_type=ContentType.objects.get_for_model(Campaign), action=Change.Actions.CREATE
        )
        self.user = factories.UserFactory.create()
        self.url = reverse("change-update", args=(self.change.uuid,))

    def test_requires_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"{reverse('account_login')}?next={self.url}", response.url)


class TestCreateView(TestCase):
    def setUp(self):
        self.user = factories.UserFactory.create()
        self.content_type = ContentType.objects.get_for_model(Season)
        self.url = reverse("change-add", args=(self.content_type.name,))

    def test_create_creates_change_instance(self):
        self.assertEqual(Change.objects.filter(content_type=self.content_type).count(), 0)
        content_type = self.content_type.id
        self.client.force_login(user=self.user)
        self.client.post(
            self.url,
            {
                "content_type": content_type,
                "action": Change.Actions.CREATE,
                "model_form-short_name": "something",
                "update": "{}",
                "model_form-long_name": "",
                "model_form-notes_internal": "",
                "model_form-notes_public": "",
                "model_form-order_priority": "",
                "model_instance_uuid": "",
            },
            follow=True,
        )
        seasons = Change.objects.filter(content_type=self.content_type)
        self.assertEqual(len(seasons), 1)

    def test_validate_does_not_create_instance(self):
        self.assertEqual(Change.objects.filter(content_type=self.content_type).count(), 0)
        content_type = self.content_type.id
        self.client.force_login(user=self.user)
        self.client.post(
            self.url,
            {
                "content_type": content_type,
                "action": Change.Actions.CREATE,
                "model_form-short_name": "something",
                "_validate": "",
                "update": "{}",
                "model_form-long_name": "",
                "model_form-notes_internal": "",
                "model_form-notes_public": "",
                "model_form-order_priority": "",
                "model_instance_uuid": "",
            },
            follow=True,
        )
        seasons = Change.objects.filter(content_type=self.content_type)
        self.assertEqual(len(seasons), 0)
