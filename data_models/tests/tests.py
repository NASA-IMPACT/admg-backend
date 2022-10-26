# to run this test file, use 'pytest -k api_app'
import pytest
from admg_webapp.users.models import User


@pytest.mark.django_db
class TestChange:
    def test_user_uuid_is_not_none(self):
        user = User.objects.create()
        assert user.uuid is not None
