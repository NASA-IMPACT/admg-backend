# to run this test file, use 'pytest -k data_models'

import pytest
from data_models.models import create_gcmd_str, remove_empties


@pytest.mark.django_db
@pytest.mark.parametrize(
    "endpoint",
    [
        "platform_type",
        "home_base",
        "repository",
        "focus_area",
        "season",
        "measurement_style",
        "measurement_type",
        "measurement_region",
        "geographical_region",
        "geophysical_concept",
        "campaign",
        "platform",
        "instrument",
        "deployment",
        "iop",
        "significant_event",
        "partner_org",
        "collection_period",
        "gcmd_phenomenon",
        "gcmd_project",
        "gcmd_platform",
        "gcmd_instrument",
        "alias",
    ],
)
class TestModels:
    pass
    # def test_get(self, client, endpoint):
    #     response = client.get(f"/api/{endpoint}", headers={"Content-Type": "application/json"})
    #     assert response.status_code == 200
    #     response_dict = response.json()
    #     assert response_dict == {"success": True, "message": "", "data": []}


class TestStandAloneFunctions:
    def test_remove_empties(self):
        with_empties = ["str1", "str2", "", None, False, [], "str3"]
        no_empties = ["str1", "str2", "str3"]

        assert remove_empties(no_empties) == no_empties  # should output an identical list
        assert (
            remove_empties(with_empties) == no_empties
        )  # should output the predefined no_empties list

    def test_create_gcmd_str(self):
        categories = ['cat1', 'cat2', 'cat3', None, ""]

        assert create_gcmd_str(categories) == 'cat1 > cat2 > cat3'
