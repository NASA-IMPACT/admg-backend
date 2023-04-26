from django.core.management import BaseCommand

from cmr.doi_matching import DoiMatcher


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--campaign-id", required=True, type=str)

    def handle(self, campaign_id, **options):
        matcher = DoiMatcher()
        matcher.generate_recommendations("campaign", campaign_id)
