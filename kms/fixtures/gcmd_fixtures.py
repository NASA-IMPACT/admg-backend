import json
import pickle
import pytest
import uuid

from data_models import models
from api_app.models import Change, CREATE, UPDATE, DELETE
from data_models.tests.factories import (
    GcmdProjectFactory,
    GcmdInstrumentFactory,
    GcmdPlatformFactory,
    GcmdPhenomenaFactory,
)


@pytest.fixture
def instrument_row():
    pickle_string = b'\x80\x04\x95\x0c\x02\x00\x00\x00\x00\x00\x00\x8c\x15django.db.models.base\x94\x8c\x0emodel_unpickle\x94\x93\x94\x8c\x0bdata_models\x94\x8c\x0eGcmdInstrument\x94\x86\x94\x85\x94R\x94}\x94(\x8c\x06_state\x94h\x00\x8c\nModelState\x94\x93\x94)\x81\x94}\x94(\x8c\x06adding\x94\x89\x8c\x02db\x94\x8c\x07default\x94\x8c\x0cfields_cache\x94}\x94ub\x8c\x04uuid\x94h\x13\x8c\x04UUID\x94\x93\x94)\x81\x94}\x94\x8c\x03int\x94\x8a\x11\x9d\xccu\xfd\x055\xf1\xaf\xd7Be\xe0\xdc\x07N\xbe\x00sb\x8c\nshort_name\x94\x8c\x04LVIS\x94\x8c\tlong_name\x94\x8c Land, Vegetation, and Ice Sensor\x94\x8c\x13instrument_category\x94\x8c Earth Remote Sensing Instruments\x94\x8c\x10instrument_class\x94\x8c\x15Active Remote Sensing\x94\x8c\x0finstrument_type\x94\x8c\nAltimeters\x94\x8c\x12instrument_subtype\x94\x8c\x16Lidar/Laser Altimeters\x94\x8c\tgcmd_uuid\x94h\x15)\x81\x94}\x94h\x18\x8a\x11\x89&\x80\x81\xac\x0e\x1f\x82\xe2N\xe65)\x843\xaa\x00sb\x8c\x0f_django_version\x94\x8c\x053.1.3\x94ub.'
    return pickle.loads(pickle_string)


@pytest.fixture(params=[GcmdProjectFactory, GcmdInstrumentFactory, GcmdPlatformFactory, GcmdPhenomenaFactory])
def gcmd_factory(request):
    return request.param


@pytest.fixture
def sync_gcmd_create_args():
    return [
        {
            "action": CREATE,
            "model": models.GcmdPhenomena,
            "uuid": None
        },
        {
            "action": UPDATE,
            "model": models.GcmdPhenomena,
            "uuid": uuid.UUID("7dea46ac-96aa-4335-a05f-e1a83072ec4f", version=4)
        },
        {
            "action": UPDATE,
            "model": models.GcmdPhenomena,
            "uuid": uuid.UUID("31d8bfd0-47db-4260-a0b1-bb632ac629bc", version=4)
        },
        None
    ]


@pytest.fixture
def sync_gcmd_delete_args():
    return (
        {
            "4f938731-d686-4d89-b72b-ff60474bb1f0",
            "16187619-9586-41e3-8faf-16981d5e6ef9",
            "cb21ad9d-7a83-482a-833d-fc3d3079a391",
            "4fb2bd9c-98ed-475d-9d9f-dfdc926e516e"
        },
        models.GcmdPhenomena
    )

mock_concepts_changes = [
    # Term shouldn't match, CREATE change record should be created.
    {
        "Term": "CALIBRATION/VALIDATION",
        "Category": "EARTH SCIENCE SERVICES",
        "Topic": "DATA ANALYSIS AND VISUALIZATION",
        "Variable_Level_1": "",
        "Variable_Level_2": "",
        "Variable_Level_3": "",
        "Detailed_Variable": "",
        "UUID": "4f938731-d686-4d89-b72b-ff60474bb1f0"
    },
    # Term that exists in DB but info doesn't match, UPDATE change record should be created.
    {
        "Term": "CALIBRATION/VALIDATION",
        "Category": "EARTH SCIENCE",
        "Topic": "DATA ANALYSIS AND VISUALIZATION",
        "Variable_Level_1": "VALIDATION",
        "Variable_Level_2": "",
        "Variable_Level_3": "",
        "Detailed_Variable": "",
        "UUID": "16187619-9586-41e3-8faf-16981d5e6ef9"
    },
    # Term that exists in DB but info doesn't match, UPDATE change record should be created.
    {
        "Term": "ANIMALS/INVERTEBRATES",
        "Category": "EARTH SCIENCE",
        "Topic": "BIOLOGICAL CLASSIFICATION",
        "Variable_Level_1": "MOLLUSKS",
        "Variable_Level_2": "CEPHALOPODS",
        "Variable_Level_3": "OCTOPUS",
        "Detailed_Variable": "",
        "UUID": "cb21ad9d-7a83-482a-833d-fc3d3079a391"
    },
    # Row should already exist with no changes.
    {
        "Term": "PRECIPITATION",
        "Category": "EARTH SCIENCE",
        "Topic": "ATMOSPHERE",
        "Variable_Level_1": "SOLID PRECIPITATION",
        "Variable_Level_2": "ICE PELLETS",
        "Variable_Level_3": "SLEET",
        "Detailed_Variable": "",
        "UUID": "4fb2bd9c-98ed-475d-9d9f-dfdc926e516e"
    }
]
