import logging

from celery import shared_task

from . import api
from api_app.models import Change
from data_models import models

logger = logging.getLogger(__name__)

concept_to_model_map = {
    "instruments": models.GcmdInstrument,
    "projects": models.GcmdProject,
    "platforms": models.GcmdPlatform,
    "sciencekeywords": models.GcmdPhenomena,
}


@shared_task
def sync_gcmd(concept_scheme: str):
    concepts = api.list_concepts(concept_scheme)
    
    # TODO: sync concepts with the DB.

    # If item not in local db but in API, create "ADD" change record
    # If item in local db but not in API, create "DELETE" change record
    # If item in local db and in API and they are not the same, create "UPDATE" change record
    
    return f"Handled {len(concepts)} {concept_scheme}"


@shared_task
def trigger_gcmd_syncs():
    """
    Triggers tasks to sync each GCMD concept of interest. Tasks are scheduled
    in a staggered fashion to reduce load on systems.
    """
    offset = 5  # Use an offset to avoid overwhelming KMS API
    for i, concept in enumerate(concept_to_model_map):
        delay = i * offset
        logger.info(f"Scheduling task to sync {concept} in {delay} seconds")
        sync_gcmd.apply_async(args=(concept,), countdown=delay, retry=False)
