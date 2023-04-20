from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from admin_ui.views.doi import update_dois

# from api_app.tests.test_change import TestChange

from admin_ui.tests import factories
from data_models.tests.factories import DOIFactory

from freezegun import freeze_time

frozen_time = datetime(2023, 4, 1, 0, 0, 0, tzinfo=timezone.utc)


class TestDoiApprovalView(TestCase):
    def setUp(self):
        self.change = factories.ChangeFactory.make_create_change_object(DOIFactory)
        self.user = factories.UserFactory.create()

    def test_requires_auth(self):
        url = reverse("doi-approval", args=(self.change.uuid,))
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"{reverse('account_login')}?next={url}", response.url)

    @freeze_time(frozen_time)
    def test_update_dois_sets_updated_at(self):
        old_updated_at = self.change.updated_at
        assert old_updated_at != frozen_time

        doi_form_value = {"uuid": self.change.uuid, "keep": True}

        update_dois(dois=[doi_form_value], user=self.user)
        self.change.refresh_from_db()
        assert self.change.updated_at == frozen_time
