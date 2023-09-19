from django.core.management.commands import loaddata
from api_app.models import Change


# Patch the loaddata command
class Command(loaddata.Command):
    """
    Change objects do certain checks to ensure that the actual database object exists.
    Sometimes dumpdata creates a file that loads in the wrong order, and these tests fail.
    This bit of code overwrites the loaddata command to write a note on the Change object
    which can be used to skip these checks.
    """

    def handle(self, *fixture_labels, **options):
        Change.loading_data = True
        super().handle(*fixture_labels, **options)
        Change.loading_data = False
