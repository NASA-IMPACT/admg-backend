from django.db import models


class ResolvedLog(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
