import json
import pickle
import pytest
import uuid

from data_models import models
from api_app.models import Change, CREATE, UPDATE, DELETE

@pytest.fixture
def convert_concept_input():
    return {
        "Bucket": "A-C",
        "Short_Name": "Test123",
        "Long_Name": "LongName123",
        "UUID": "07a12d76-3794-4d1f-8db3-96a4c9814d54"
    }

@pytest.fixture
def convert_concept_result():
    return {
        "bucket": "A-C",
        "short_name": "Test123",
        "long_name": "LongName123",
        "gcmd_uuid": "07a12d76-3794-4d1f-8db3-96a4c9814d54"
    }

@pytest.fixture
def compare_record_with_concept_row():
    pickle_string = b'\x80\x04\x95\x0c\x02\x00\x00\x00\x00\x00\x00\x8c\x15django.db.models.base\x94\x8c\x0emodel_unpickle\x94\x93\x94\x8c\x0bdata_models\x94\x8c\x0eGcmdInstrument\x94\x86\x94\x85\x94R\x94}\x94(\x8c\x06_state\x94h\x00\x8c\nModelState\x94\x93\x94)\x81\x94}\x94(\x8c\x06adding\x94\x89\x8c\x02db\x94\x8c\x07default\x94\x8c\x0cfields_cache\x94}\x94ub\x8c\x04uuid\x94h\x13\x8c\x04UUID\x94\x93\x94)\x81\x94}\x94\x8c\x03int\x94\x8a\x11\x9d\xccu\xfd\x055\xf1\xaf\xd7Be\xe0\xdc\x07N\xbe\x00sb\x8c\nshort_name\x94\x8c\x04LVIS\x94\x8c\tlong_name\x94\x8c Land, Vegetation, and Ice Sensor\x94\x8c\x13instrument_category\x94\x8c Earth Remote Sensing Instruments\x94\x8c\x10instrument_class\x94\x8c\x15Active Remote Sensing\x94\x8c\x0finstrument_type\x94\x8c\nAltimeters\x94\x8c\x12instrument_subtype\x94\x8c\x16Lidar/Laser Altimeters\x94\x8c\tgcmd_uuid\x94h\x15)\x81\x94}\x94h\x18\x8a\x11\x89&\x80\x81\xac\x0e\x1f\x82\xe2N\xe65)\x843\xaa\x00sb\x8c\x0f_django_version\x94\x8c\x053.1.3\x94ub.'
    return pickle.loads(pickle_string)

@pytest.fixture
def compare_record_with_concept_dict():
    return {
        "short_name": "LVIS",
        "long_name": "Land, Vegetation, and Ice Sensor",
        "instrument_category": "Earth Remote Sensing Instruments",
        "instrument_class": "Active Remote Sensing",
        "instrument_type": "Altimeters",
        "instrument_subtype": "Lidar/Laser Altimeters",
        "gcmd_uuid": "aa338429-35e6-4ee2-821f-0eac81802689"
    }

@pytest.fixture
def delete_old_records_uuids():
    return {
        "delete_gcmd_uuids": ["16187619-9586-41e3-8faf-16981d5e6ef9", "03c9e37e-d162-43f2-824d-ad4dca88080e"],
        "change_model_uuids": ["eaa1cffc-81d8-4131-a1ba-418a8dfe07e7", "05f36a80-e5b0-4014-96a0-ad6183011da5"]
    }

@pytest.fixture(params=["test1", "test2"])
def get_change_record_inputs(request):
    inputs = {
        "test1": {
            "concept": {
                "short_name": "instr-change",
                "long_name": "instrument-change",
                "instrument_category": "committee",
                "gcmd_uuid": "690b684a-0857-4264-b9b3-d6c60f07ae02"
            },
            "action": CREATE,
            "model": models.GcmdInstrument,
            "model_uuid": None,
            "exists": True
        },
        "test2": {
            "concept": {
                "short_name": "OLI/TIRS",
                "long_name": "Landsat 8 OLI/TIRS",
                "instrument_category": "Earth Remote Sensing Instruments",
                "gcmd_uuid": "7e74257a-f59f-4591-8530-93bbaf39c7cd"
            },
            "action": CREATE,
            "model": models.GcmdInstrument,
            "model_uuid": None,
            "exists": True
        }
    }
    return inputs[request.param]

@pytest.fixture
def get_change_concept(get_change_record_inputs):
    return get_change_record_inputs["concept"]

@pytest.fixture
def get_change_model(get_change_record_inputs):
    return get_change_record_inputs["model"]

@pytest.fixture
def get_change_action(get_change_record_inputs):
    return get_change_record_inputs["action"]

@pytest.fixture
def get_change_model_uuid(get_change_record_inputs):
    return get_change_record_inputs["model_uuid"]

@pytest.fixture
def get_change_exists(get_change_record_inputs):
    return get_change_record_inputs["exists"]

@pytest.fixture(params=["createTest1", "updateTest1", "updateTest2", "deleteTest1"])
def create_change_data(request):
    data = {
        "createTest1": {
            "input": {
                "concept": {
                    "term": "CALIBRATION/VALIDATION",
                    "category": "EARTH SCIENCE SERVICES",
                    "topic": "DATA ANALYSIS AND VISUALIZATION",
                    "gcmd_uuid": "4f938731-d686-4d89-b72b-ff60474bb1f0"
                },
                "model": models.GcmdPhenomena,
                "action": CREATE,
                "model_uuid": None
            },
            "new_row": True
        },
        "updateTest1": {
            "input": {
                "concept": {
                    "term": "ANIMALS/INVERTEBRATES",
                    "category": "EARTH SCIENCE",
                    "topic": "BIOLOGICAL CLASSIFICATION",
                    "variable_1": "MOLLUSKS",
                    "variable_2": "CEPHALOPODS",
                    "variable_3": "OCTOPUS",
                    "gcmd_uuid": "cb21ad9d-7a83-482a-833d-fc3d3079a391"
                },
                "model": models.GcmdPhenomena,
                "action": UPDATE,
                "model_uuid": "31d8bfd0-47db-4260-a0b1-bb632ac629bc"
            },
            "new_row": True
        },
        # This test will reuse a change record that is already in the database.
        "updateTest2": {
            "input": {
                "concept": {
                    "short_name": "HALO",
                    "long_name": "High Altitude Lidar Observatory",
                    "instrument_category": "Earth Remote Sensing Instruments",
                    "instrument_class": "Active Remote Sensing",
                    "instrument_type": "Altimeters",
                    "instrument_subtype": "Lidar/Laser Altimeters",
                    "gcmd_uuid": "16187619-9586-41e3-8faf-16981d5e6ef9"
                },
                "model": models.GcmdInstrument,
                "action": UPDATE,
                "model_uuid": "ff6d19df-87c9-42a5-8704-399c65acf2ff"
            },
            "new_row": False
        },
        "deleteTest1": {
            "input": {
                "concept": {
                    "gcmd_uuid": "8c868eeb-b935-4eab-9abf-e6f4dde70fdf"
                },
                "model": models.GcmdInstrument,
                "action": DELETE,
                "model_uuid": "eaa1cffc-81d8-4131-a1ba-418a8dfe07e7"
            },
            "new_row": True
        }
    }
    return data[request.param]

@pytest.fixture
def create_change_input(create_change_data):
    return create_change_data["input"]

@pytest.fixture
def create_change_new_row(create_change_data):
    return create_change_data["new_row"]

@pytest.fixture(params=["validProject1", "validProject2", "invalidProject1", "invalidProject2", "invalidProject3", "invalidProject4", "invalidProject5"])
def is_valid_concept_input(request):
    inputs = {
        "validProject1": {
            "concept": {
                "Bucket": "A-B",
                "Short_Name": "abc123",
                "Long_Name": "",
                "UUID": "80b0db10-fe44-4d15-b66c-374476e8c93b"
            },
            "model": models.GcmdProject,
            "result": True
        },
        "validProject2": {
            "concept": {
                "Bucket": "A-Z",
                "Short_Name": "project123",
                "Long_Name": "Long Project Name",
                "UUID": "32ccf67d-e2e1-4fe9-b17d-08bfd6bf1ba3"
            },
            "model": models.GcmdProject,
            "result": True
        },
        "invalidProject1": {
            "concept": {},
            "model": models.GcmdProject,
            "result": False
        },
        "invalidProject2": {
            "concept": {
                "Bucket": "A-C",
                "Short_Name": "",
                "Long_Name": "Long Project Name",
                "UUID": "58c2f733-c316-4991-ae9d-d936a75ce365"
            },
            "model": models.GcmdProject,
            "result": False
        },
        "invalidProject3": {
            "concept": {
                "Bucket": "A-C",
                "Short_Name": "",
                "Long_Name": "Long Project Name",
                "UUID": "58c2f733-c316-4991-ae9d-d936a75ce365"
            },
            "model": models.GcmdProject,
            "result": False
        },
        "invalidProject4": {
            "concept": {
                "Bucket": "  NOT APPLICABLE ",
                "Short_Name": "Project123",
                "Long_Name": "Long Project Name",
                "UUID": "58c2f733-c316-4991-ae9d-d936a75ce365"
            },
            "model": models.GcmdProject,
            "result": False
        },
        "invalidProject5": {
            "concept": {
                "Bucket": "A-C",
                "Short_Name": "Project123",
                "Long_Name": "Long Project Name",
                "UUID": "58c2f733-c316-4991-"
            },
            "model": models.GcmdProject,
            "result": False
        }
    }
    return inputs[request.param]

@pytest.fixture
def is_valid_concept(is_valid_concept_input):
    return is_valid_concept_input["concept"]

@pytest.fixture
def is_valid_model(is_valid_concept_input):
    return is_valid_concept_input["model"]

@pytest.fixture
def is_valid_result(is_valid_concept_input):
    return is_valid_concept_input["result"]

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
