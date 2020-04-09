from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, IntegerField
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

ADMIN = 'Admin'
STAFF = 'Staff'

AVAILABLE_ROLES = ((1, ADMIN), (2, STAFF))


# TODO: Once the models are reviwed, use the roles part of the users to
# validate with Authorization part.
# See dummy api for implementaion using oauth scopes
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
    
    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = 1
        super().save(*args, **kwargs)
