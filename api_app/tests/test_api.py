import pytest


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
class TestApi:
    def test_get(self, client, endpoint):
        response = client.get(f"/api/{endpoint}", headers={"Content-Type": "application/json"})
        assert response.status_code == 200
        response_dict = response.json()
        assert response_dict == {"success": True, "message": "", "data": []}

    def test_post_arent_public(self, client, endpoint):
        response = client.post(
            f"/api/{endpoint}", data={}, headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401
        response_dict = response.json()
        assert response_dict == {"detail": "Authentication credentials were not provided."}
