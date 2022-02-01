import logging
from celery import shared_task

from . import api, gcmd
from api_app.models import Change, CREATE, UPDATE, DELETE, PATCH, IN_ADMIN_REVIEW_CODE 
from data_models import models

logger = logging.getLogger(__name__)


@shared_task
def sync_gcmd(concept_scheme: str) -> str:
    """This function aims to sync the gcmd API with the gcmd database by doing the following:
        # If item not in local db but in API, create "ADD" change record
        # If item in local db but not in API, create "DELETE" change record
        # If item in local db and in API and they are not the same, create "UPDATE" change record
    """
    model = gcmd.concept_to_model_map[concept_scheme]
    concepts = api.list_concepts(concept_scheme)
    uuids = set([concept.get("UUID") for concept in concepts])
    for concept in concepts:
        if not gcmd.is_valid_record(concept, model):
            continue
        concept = gcmd.convert_record(concept, model)

        try:
            row = model.objects.get(gcmd_uuid=concept["gcmd_uuid"])
        except model.DoesNotExist:
            # If item not in db but in API, create "ADD" change record
            gcmd.create_change(concept, model, CREATE, None)
        else:
            # Compare api record to record in db to see if they match. If they are the same, then we are done for this record.
            if not gcmd.compare_record_with_concept(row, concept):
                # If item in db and in API do not match, create "UPDATE" change record
                gcmd.create_change(concept, model, UPDATE, row.uuid)

    gcmd.delete_old_records(uuids, model)

    return f"Handled {len(concepts)} {concept_scheme}"


@shared_task
def trigger_gcmd_syncs() -> None:
    """
    Triggers tasks to sync each GCMD concept of interest. Tasks are scheduled
    in a staggered fashion to reduce load on systems.
    """
    offset = 5  # Use an offset to avoid overwhelming KMS API
    for i, concept in enumerate(gcmd.concept_to_model_map):
        delay = i * offset
        logger.info(f"Scheduling task to sync {concept} in {delay} seconds")
        sync_gcmd.apply_async(args=(concept, ), countdown=delay, retry=False)
