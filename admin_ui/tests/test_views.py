from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from admg_webapp.users.models import User
from admin_ui.views.change import CampaignDetailView
from api_app.models import Change
from data_models.models import Campaign, Season

from . import factories
from api_app.tests import TestChange
from data_models.tests.factories import CampaignFactory


class TestChangeUpdateView(TestCase):
    def setUp(self):
        self.change = TestChange.make_create_change_object(CampaignFactory)
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


class TestCampaignDetailView(TestCase):
    def setUp(self):
        # admin is needed to force publish without the intervening steps
        self.user = factories.UserFactory.create(role=User.Roles.ADMIN)
        self.create_change = TestChange.make_create_change_object(CampaignFactory)
        self.create_change.publish(self.user)

        self.update_changes = []
        for _ in range(10):
            update_change = factories.ChangeFactory.create(
                content_type=ContentType.objects.get_for_model(Campaign),
                action=Change.Actions.UPDATE,
                model_instance_uuid=self.create_change.uuid,
            )
            update_change.publish(self.user)
            self.update_changes.append(update_change)

    def test_filter_latest_changes_returns_latest_change(self):
        """
        Only the latest Change object should be returned for the queryset.
        """
        latest = CampaignDetailView._filter_latest_changes(
            Change.objects.of_type(Campaign)
            .filter(model_instance_uuid=str(self.create_change.uuid))
            .prefetch_approvals()
        )
        self.assertEqual(latest[0].uuid, self.update_changes[-1].uuid)

    def test_filter_latest_changes_with_multiple_models_returns_latest_change(self):
        """
        If multiple campaigns are referenced in the queryset, the
        method should return the latest Change object for each Campaign.
        """

        create_change = TestChange.make_create_change_object(CampaignFactory)
        create_change.publish(self.user)

        update_changes = []
        for _ in range(10):
            update_change = factories.ChangeFactory.create(
                content_type=ContentType.objects.get_for_model(Campaign),
                action=Change.Actions.UPDATE,
                model_instance_uuid=create_change.uuid,
            )
            update_change.publish(self.user)
            update_changes.append(update_change)

        latest = CampaignDetailView._filter_latest_changes(
            Change.objects.of_type(Campaign).prefetch_approvals()
        )
        self.assertTrue(self.update_changes[-1].uuid in [change.uuid for change in latest])
        self.assertTrue(update_changes[-1].uuid in [change.uuid for change in latest])
