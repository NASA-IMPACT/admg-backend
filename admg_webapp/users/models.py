from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, IntegerField
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

ADMIN = 'Admin'
STAFF = 'Staff'

ADMIN_CODE = 1
STAFF_CODE = 2
AVAILABLE_ROLES = ((ADMIN_CODE, ADMIN), (STAFF_CODE, STAFF))


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
            self.role = ADMIN_CODE
        super().save(*args, **kwargs)
