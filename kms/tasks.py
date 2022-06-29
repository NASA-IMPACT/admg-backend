import logging
from celery import shared_task

from kms import api, gcmd

from api_app.models import Change

logger = logging.getLogger(__name__)


@shared_task
def sync_gcmd(keyword_scheme: str) -> str:
    """This function aims to sync the gcmd public dataset with the gcmd database by doing the following:
    * If item not in db but in API, create "ADD" change record
    * If item in db and in API do not match, create "UPDATE" change record
    * If item in db but not in API, create "DELETE" change record
    """
    model = gcmd.keyword_to_model_map[keyword_scheme]
    keywords = api.list_keywords(keyword_scheme)
    uuids = set([keyword.get("UUID") for keyword in keywords])

    for keyword in keywords:
        if not gcmd.is_valid_keyword(keyword, model):
            continue
        keyword = gcmd.convert_keyword(keyword, model)
        try:
            row = model.objects.get(gcmd_uuid=keyword["gcmd_uuid"])
        except model.DoesNotExist:
            # If item not in db but in API, create "ADD" change record
            gcmd.create_change(keyword, model, Change.Actions.CREATE, None)
        else:
            # Compare api record to record in db to see if they match. If they are the same, then we are done for this record.
            if not gcmd.compare_record_with_keyword(row, keyword):
                # If item in db and in API do not match, create "UPDATE" change record
                gcmd.create_change(keyword, model, Change.Actions.UPDATE, row.uuid)

    gcmd.delete_keywords_from_current_uuids(uuids, model)

    return f"Handled {len(keywords)} {keyword_scheme}"


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


if __name__ == "__main__":
    sync_gcmd("sciencekeywords")
