# to run this test file, use 'pytest -k data_models'

# import pytest
from data_models import models

models = [
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

# searchable_names_defaults = ['short_name', 'long_name']

# searchable_names_mapping = {
#     'GcmdPhenomenon': [
#         'category',
#         'topic',
#         'term',
#         'variable_1',
#         'variable_2',
#         'variable_3',
#     ],
#     'Website': ['url', 'title'],
#     'IOP': ['short_name'],
#     'SignificantEvent': ['short_name'],
# }

# searchable_names_list = []
# for model in models:
#     if model in searchable_names_mapping.keys():
#         model_fields = {'model_name': model, 'searchable_fields': searchable_names_mapping[model]}
#     else:
#         model_fields = {'model_name': model, 'searchable_fields': searchable_names_defaults}
#     searchable_names_list.append(model_fields)


# @pytest.mark.django_db
# @pytest.mark.parametrize("searchable_names", searchable_names_list)
# class TestModels:
#     def test_searchable_names(self, searchable_names):
#         """
#         So, the searchable names should do two things:
#             - if the model has an alias attachement, go get the list of alias short names
#             - if the model has a list of additional relevant names, go get them
#             - combine these two lists into a mega list for searching

#         So, there should be a function that does the alias thing and also takes a list
#         So, the base class defines the list of names default names and the function uses that list
#         The child classes overwrite that list
#         """

# def test_get(self, client, endpoint):
#     response = client.get(f"/api/{endpoint}", headers={"Content-Type": "application/json"})
#     assert response.status_code == 200
#     response_dict = response.json()
#     assert response_dict == {"success": True, "message": "", "data": []}


class TestStandAloneFunctions:

    def test_create_gcmd_str(self):
        categories = ['cat1', 'cat2', 'cat3', None, ""]

        assert models.create_gcmd_str(categories) == 'cat1 > cat2 > cat3'


test will take in each model. each model will crossrefernce the test refernce data. it will be a dict, with the model name and a list of 

for model_name in model_names:
    model_name.objects.first().custom_search_fields()

from data_models import models
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

{model:getattr(models, model).objects.first().custom_search_fields() for model in model_names}