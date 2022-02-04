import json
import pickle
import pytest

from data_models import models
from api_app.models import Change, CREATE, UPDATE, DELETE

def open_json_file(filepath):
    return json.load(open(filepath, 'r'))

def open_pickle_file(filepath):
    return pickle.load(open(filepath, 'rb'))

@pytest.fixture
def convert_record_input():
    return {
        "Bucket": "A-C",
        "Short_Name": "Test123",
        "Long_Name": "LongName123",
        "UUID": "07a12d76-3794-4d1f-8db3-96a4c9814d54"
    }

@pytest.fixture
def convert_record_result():
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
def check_change_records_inputs(request):
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
def check_concept(check_change_records_inputs):
    return check_change_records_inputs["concept"]

@pytest.fixture
def check_action(check_change_records_inputs):
    return check_change_records_inputs["action"]

@pytest.fixture
def check_model(check_change_records_inputs):
    return check_change_records_inputs["model"]

@pytest.fixture
def check_model_uuid(check_change_records_inputs):
    return check_change_records_inputs["model_uuid"]

@pytest.fixture
def check_exists(check_change_records_inputs):
    return check_change_records_inputs["exists"]

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
            "outcome": True
        },
        "validProject2": {
            "concept": {
                "Bucket": "A-Z",
                "Short_Name": "project123",
                "Long_Name": "Long Project Name",
                "UUID": "32ccf67d-e2e1-4fe9-b17d-08bfd6bf1ba3"
            },
            "model": models.GcmdProject,
            "outcome": True
        },
        "invalidProject1": {
            "concept": {},
            "model": models.GcmdProject,
            "outcome": False
        },
        "invalidProject2": {
            "concept": {
                "Bucket": "A-C",
                "Short_Name": "",
                "Long_Name": "Long Project Name",
                "UUID": "58c2f733-c316-4991-ae9d-d936a75ce365"
            },
            "model": models.GcmdProject,
            "outcome": False
        },
        "invalidProject3": {
            "concept": {
                "Bucket": "A-C",
                "Short_Name": "",
                "Long_Name": "Long Project Name",
                "UUID": "58c2f733-c316-4991-ae9d-d936a75ce365"
            },
            "model": models.GcmdProject,
            "outcome": False
        },
        "invalidProject4": {
            "concept": {
                "Bucket": "  NOT APPLICABLE ",
                "Short_Name": "Project123",
                "Long_Name": "Long Project Name",
                "UUID": "58c2f733-c316-4991-ae9d-d936a75ce365"
            },
            "model": models.GcmdProject,
            "outcome": False
        },
        "invalidProject5": {
            "concept": {
                "Bucket": "A-C",
                "Short_Name": "Project123",
                "Long_Name": "Long Project Name",
                "UUID": "58c2f733-c316-4991-"
            },
            "model": models.GcmdProject,
            "outcome": False
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
def is_valid_outcome(is_valid_concept_input):
    return is_valid_concept_input["outcome"]

mock_concepts = [
  {
    "Basis": "Space Stations/Crewed Spacecraft",
    "Category": "",
    "Sub_Category": "",
    "Short_Name": "MIR-PRIRODA",
    "Long_Name": "PRIRODA Module of MIR Space Station",
    "UUID": "207e6805-2bdf-4954-8178-c4cd63ce2269"
  },
  {
    "Basis": "Space Stations/Crewed Spacecraft",
    "Category": "",
    "Sub_Category": "",
    "Short_Name": "OSTA-1",
    "Long_Name": "Office of Space & Terrestrial Applications-1",
    "UUID": "e554b6aa-8d53-4fc5-a7d3-e43808d9e41b"
  },
  {
    "Basis": "Space Stations/Crewed Spacecraft",
    "Category": "",
    "Sub_Category": "",
    "Short_Name": "SKYLAB",
    "Long_Name": "",
    "UUID": "b0f992d7-3ff5-4470-849a-a540a9f8ce3e"
  },
  {
    "Basis": "Space Stations/Crewed Spacecraft",
    "Category": "",
    "Sub_Category": "",
    "Short_Name": "SOYUZ",
    "Long_Name": "",
    "UUID": "0a14ea80-5b3a-4d6f-a81b-38150a1fbe93"
  },
  {
    "Basis": "Space Stations/Crewed Spacecraft",
    "Category": "",
    "Sub_Category": "",
    "Short_Name": "",
    "Long_Name": "",
    "UUID": "388e72a1-b851-4b78-9e69-747e06ae215f"
  }
]
