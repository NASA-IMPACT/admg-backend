from api_app.models import Change
from celery import shared_task
from dataclasses import asdict
from django.template.loader import get_template
from kms import gcmd, email
from typing import List
import logging

logger = logging.getLogger(__name__)

def serialize(sync):
    print(f"Sync: {sync}")
    temp = {}
    for field in sync:
        print(f"FIELD: {field}")
        if field[0] == "create_keywords":
            temp["create_keywords"] = field[1]
        elif field[0] == "update_keywords":
            temp["update_keywords"] = field[1]
        elif field[0] == "delete_keywords":
            temp["delete_keywords"] = field[1]
        elif field[0] == "published_keywords":
            temp["published_keywords"] = field[1]

    return temp

@shared_task
def email_gcmd_sync_results(gcmd_syncs):
    keywords_by_scheme, autopublished_keywords = [], []
    for scheme, sync in gcmd_syncs.items():
        published_keywords = Change.objects.filter(uuid__in=sync["published_keywords"])
        autopublished_keywords.extend(published_keywords)

        # Get keywords for each type of change, exclude keywords that were published.
        create_keywords = Change.objects.filter(uuid__in=sync["create_keywords"]).difference(published_keywords)
        update_keywords = Change.objects.filter(uuid__in=sync["update_keywords"]).difference(published_keywords)
        delete_keywords = Change.objects.filter(uuid__in=sync["delete_keywords"]).difference(published_keywords)
        keywords_by_scheme.append({
            "scheme": scheme,
            "create_keywords": create_keywords,
            "update_keywords": update_keywords,
            "delete_keywords": delete_keywords,
            "published_keywords": published_keywords,
            "scheme_count": len(create_keywords) + len(update_keywords) + len(delete_keywords) + len(published_keywords),
        })
    total_count = sum([keyword['scheme_count'] for keyword in keywords_by_scheme])
    print(f"Keywords By Scheme: {keywords_by_scheme}")
    email.gcmd_changes_email(
        email.Template(
            "gcmd_notification.html",
            f"GCMD Sync - {total_count} Changes Found!",
            {
                "keywords_by_scheme": keywords_by_scheme,
                "total_count": total_count,
                "autopublished_keywords": autopublished_keywords
            },
        ),
        ["john@developmentseed.org"]
    )

@shared_task
def sync_gcmd() -> str:
    gcmd_syncs = {}
    for keyword_scheme in gcmd.scheme_to_model_map:
        sync = gcmd.GcmdSync(keyword_scheme)
        logger.info(sync.sync_keywords())
        gcmd_syncs[keyword_scheme] = asdict(sync, dict_factory=serialize)
    # print(f"Syncs IN SYNC TASK: {gcmd_syncs}")

    # TOOD: Figure out countdown value
    email_gcmd_sync_results.apply_async(args=(gcmd_syncs,), countdown=1, retry=False)
