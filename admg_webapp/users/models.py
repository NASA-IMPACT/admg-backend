import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField, IntegerField
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class User(AbstractUser):
    """
    user model for admg users
    """

    class Roles(models.IntegerChoices):
        ADMIN = 1, "Admin"
        STAFF = 2, "Staff"

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = CharField(_("Name of User"), max_length=255)
    role = IntegerField(choices=Roles.choices, default=Roles.STAFF)

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = User.Roles.ADMIN
        super().save(*args, **kwargs)

    def is_admg_admin(self):
        return self.role == User.Roles.ADMIN
