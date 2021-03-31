from time import sleep

from django.core.management.base import BaseCommand, CommandError

from config.celery_app import debug_task


class Command(BaseCommand):
    """
        Runs the defaut celery debug task to test celery functionality.
        Call from the main folder with "python manage.py checkcelery"
        Expected output is "SUCCESS" printed to the terminal.
    """

    def handle(self, *args, **options):
        response = debug_task.delay()
        sleep(0.1)
        print(response.status)