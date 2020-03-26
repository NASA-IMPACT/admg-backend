from django.db import models

# Create your models here.


class DummyModel(models.Model):
    test1 = models.CharField(verbose_name='testing 1', max_length=15, blank=True)
    test2 = models.CharField(verbose_name='testing 2', max_length=15)
    test3 = models.IntegerField(verbose_name='testing 3')
