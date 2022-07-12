import logging
from celery import shared_task

from kms import api, gcmd

from api_app.models import Change

logger = logging.getLogger(__name__)


@shared_task
def sync_gcmd(keyword_scheme: str) -> str:
    sync = gcmd.GcmdSync(keyword_scheme)
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
