from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, IntegerField
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

AVAILABLE_ROLES = ((1, 'Admin'), (2, 'Staff'))


class User(AbstractUser):
    """
    user model for admg users
    """

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = CharField(_("Name of User"), max_length=255)
    role = IntegerField(choices=AVAILABLE_ROLES, default=2)

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})
