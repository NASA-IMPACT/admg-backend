import logging
from celery import shared_task
from django.template.loader import get_template
from typing import List
from api_app.models import Change

from kms import gcmd, email

logger = logging.getLogger(__name__)


@shared_task
def email_gcmd_sync_results(create_uuids: List[str], update_uuids: List[str], delete_uuids: List[str]):
    create_keywords = Change.objects.filter(uuid__in=create_uuids)
    update_keywords = Change.objects.filter(uuid__in=update_uuids)
    delete_keywords = Change.objects.filter(uuid__in=delete_uuids)
    print(f"Create UUIDs: {create_uuids}")
    print(f"Create Keywords: {create_keywords}")
    email.gcmd_changes_email(
        email.Template("gcmd_notification.html", "GCMD Sync Changes Found",
        {
            "create_keywords": create_keywords,
            "update_keywords": update_keywords,
            "delete_keywords": delete_keywords
        }),
        ["john@developmentseed.org"]
    )


@shared_task
def sync_gcmd(keyword_scheme: str) -> str:
    sync = gcmd.GcmdSync(keyword_scheme)
    email_gcmd_sync_results.apply_async(args=(sync.create_keywords, sync.update_keywords, sync.delete_keywords), countdown=1, retry=False)
    logger.info(sync.sync_keywords())


@shared_task
def trigger_gcmd_syncs() -> None:
    """
    Triggers tasks to sync each GCMD keyword of interest. Tasks are scheduled
    in a staggered fashion to reduce load on systems.
    """
    offset = 5  # Use an offset to avoid overwhelming KMS API
    for i, keyword in enumerate(gcmd.keyword_to_model_map):
        delay = i * offset
        logger.info(f"Scheduling task to sync {keyword} in {delay} seconds")
        sync_gcmd.apply_async(args=(keyword,), countdown=delay, retry=False)
