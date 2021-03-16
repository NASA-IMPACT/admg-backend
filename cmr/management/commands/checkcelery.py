from time import sleep

from django.core.management.base import BaseCommand, CommandError

from config.celery_app import debug_task


class Command(BaseCommand):
    """
        Creates a new super user if one doesn't exist
    """
    def handle(self, *args, **options):
        response = debug_task.delay()
        sleep(0.1)
        print(response.status)
