from celery import shared_task
from cmr.doi_matching import DoiMatcher
from data_models.website_analyzer import run_validator_and_store


@shared_task
def validate_websites_and_store():
    return run_validator_and_store()


@shared_task
def match_dois(table_name, uuid):
    matcher = DoiMatcher()
    return matcher.generate_recommendations(table_name, uuid)


@shared_task
def add(a, b):
    return a + b
