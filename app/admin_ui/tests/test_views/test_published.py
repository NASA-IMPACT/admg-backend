import pytest
from django.urls import reverse

from admin_ui.tables.tables import ShortNamefromUUIDColumn
from admin_ui.tests.factories import ChangeFactory
from data_models.tests.factories import CampaignFactory
from data_models.models import Campaign


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model_name",
    [
        "campaign",
        "doi",
        "collection_period",
    ],
)
class TestPublished:
    def test_get(self, client, model_name):
        url = reverse("published-list", args=(model_name,))
        response = client.get(url)
        assert 200 == response.status_code


@pytest.mark.django_db
class TestShortNameFromUUIDColumn:
    def test_get_names_from_concrete_model(self):
        campaign = CampaignFactory()
        column = ShortNamefromUUIDColumn(Campaign)
        assert column.get_short_names([str(campaign.uuid)])[0] == campaign.short_name

    def test_get_name_from_concrete_model(self):
        campaign = CampaignFactory()
        column = ShortNamefromUUIDColumn(Campaign)
        assert column.get_short_name(str(campaign.uuid)) == campaign.short_name

    def test_get_names_from_change_model(self):
        change = ChangeFactory.make_create_change_object(
            CampaignFactory, custom_fields={"short_name": "test"}
        )
        column = ShortNamefromUUIDColumn(Campaign)
        assert column.get_short_names([str(change.uuid)])[0] == change.update["short_name"]

    def test_get_name_from_change_model(self):
        change = ChangeFactory.make_create_change_object(
            CampaignFactory, custom_fields={"short_name": "test"}
        )
        column = ShortNamefromUUIDColumn(Campaign)
        assert column.get_short_name(str(change.uuid)) == change.update["short_name"]

    def test_get_names_from_non_uuid_values(self):
        """
        Should return the provided values intact
        """
        column = ShortNamefromUUIDColumn(Campaign)
        assert column.get_short_names(["test"]) == ["test"]

    def test_get_name_from_non_uuid_value(self):
        """
        Should return the provided value intact
        """
        column = ShortNamefromUUIDColumn(Campaign)
        assert column.get_short_name("test") == "test"
