from django.db import models


class AdminPermission(models.Model):
    # https://stackoverflow.com/a/37988537/728583

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (("can_deploy", "Permissions to deploy website"),)
