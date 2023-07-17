# to run this test file, use 'pytest -k data_models'

import pytest
from data_models import models
import json

model_names = [
    "PlatformType",
    "HomeBase",
    "Repository",
    "FocusArea",
    "Season",
    "MeasurementStyle",
    "MeasurementType",
    "MeasurementRegion",
    "GeographicalRegion",
    "GeophysicalConcept",
    "Campaign",
    "Platform",
    "Instrument",
    "Deployment",
    "IOP",
    "SignificantEvent",
    "PartnerOrg",
    "CollectionPeriod",
    "GcmdPhenomenon",
    "GcmdProject",
    "GcmdPlatform",
    "GcmdInstrument",
    "Alias",
]


class TestStandAloneFunctions:
    def test_create_gcmd_str(self):
        categories = ['cat1', 'cat2', 'cat3', None, ""]

        assert models.create_gcmd_str(categories) == 'cat1 > cat2 > cat3'


@pytest.mark.parametrize("model_name", model_names)
class TestModelFunctions:
    def test_custom_search_fields(self, model_name):
        """Each model has a known list of fields or related fields that contain vaid names, such as short_name,
        long_name, aliases, and various custom fields. The function being tested should output the correct list
        for each model. We have a hard copy of the expected fields to test against.
        """
        custom_search_fields = json.load(open('data_models/tests/custom_search_fields.json'))
        model = getattr(models, model_name)

        assert model.custom_search_fields(model) == custom_search_fields[model_name]
