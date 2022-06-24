import logging
from celery import shared_task

from . import gcmd
from api_app.models import Change

logger = logging.getLogger(__name__)


@shared_task
def sync_gcmd(concept_scheme: str) -> str:
    # fmt: off
    """This function aims to sync the gcmd public dataset with the gcmd database by doing the following:
        * If item not in db but in API, create "ADD" change record
        * If item in db and in API do not match, create "UPDATE" change record
        * If item in db but not in API, create "DELETE" change record
    """
    # fmt: on

    # TODO: Take out!
    import csv

    model = gcmd.concept_to_model_map[concept_scheme]
    # TODO: Change back!
    # concepts = api.list_concepts(concept_scheme)
    with open("/Users/john/projects/admg_webapp/john/csv/gcmdphenomena.csv") as concept_file:
        concepts = list(csv.DictReader(concept_file.readlines()))
        print(f"Concepts: {concepts}")
    uuids = set([concept.get("UUID") for concept in concepts])
    # TODO: Put this in its own function!
    for concept in concepts:
        if not gcmd.is_valid_concept(concept, model):
            continue
        concept = gcmd.convert_concept(concept, model)
        try:
            row = model.objects.get(gcmd_uuid=concept["gcmd_uuid"])
        except model.DoesNotExist:
            # If item not in db but in API, create "ADD" change record
            gcmd.create_change(concept, model, Change.Actions.CREATE, None)
        else:
            # Compare api record to record in db to see if they match. If they are the same, then we are done for this record.
            if not gcmd.compare_record_with_concept(row, concept):
                # If item in db and in API do not match, create "UPDATE" change record
                gcmd.create_change(concept, model, Change.Actions.UPDATE, row.uuid)

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
        sync_gcmd.apply_async(args=(concept,), countdown=delay, retry=False)


if __name__ == "__main__":
    sync_gcmd("sciencekeywords")
