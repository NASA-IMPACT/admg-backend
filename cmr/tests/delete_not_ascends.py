from api_app.models import Change
from data_models import models

model_names = [
    "PlatformType",
    "MeasurementType",
    "MeasurementStyle",
    "FocusArea",
    "Season",
    "Repository",
    "MeasurementRegion",
    "GeographicalRegion",
    "GeophysicalConcept",
    "PartnerOrg",
    "GcmdProject",
    "GcmdPhenomenon",
    "GcmdInstrument",
    "GcmdPlatform",
    "DOI",
    "Campaign",
    "Platform",
    "Deployment",
    "IOP",
    "SignificantEvent",
    "CollectionPeriod",
    "Instrument",
    "Alias",
    "Image",
    "Website",
    "WebsiteType",
]


def delete_if_not_in_db(model):
    for draft in Change.objects.of_type(model):
        if draft.model_instance_uuid not in model.objects.all().values_list("uuid", flatten=True):
            draft.delete()


# remove all campaigns except ASCENDS
models.Campaign.objects.exclude(short_name='ASCENDS Airborne').delete()

# TODO: remove instruments, gcmd, etc not linked to ascends

for model_name in model_names:
    model = getattr(models, model_name)
    delete_if_not_in_db(model)
