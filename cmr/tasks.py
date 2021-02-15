from celery import shared_task
from cmr.doi_matching import DoiMatcher

@shared_task
def match_dois(table_name, uuid):
    matcher = DoiMatcher()
    return matcher.generate_recommendations(table_name, uuid)
