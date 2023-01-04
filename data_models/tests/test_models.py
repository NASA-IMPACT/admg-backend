# to run this test file, use 'pytest -k data_models'

# import pytest
from data_models.models import create_gcmd_str

# models = [
#     "platform_type",
#     "home_base",
#     "repository",
#     "focus_area",
#     "season",
#     "measurement_style",
#     "measurement_type",
#     "measurement_region",
#     "geographical_region",
#     "geophysical_concept",
#     "campaign",
#     "platform",
#     "instrument",
#     "deployment",
#     "iop",
#     "significant_event",
#     "partner_org",
#     "collection_period",
#     "gcmd_phenomenon",
#     "gcmd_project",
#     "gcmd_platform",
#     "gcmd_instrument",
#     "alias",
# ]

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
    # def test_remove_empties(self):
    #     with_empties = ["str1", "str2", "", None, False, [], "str3"]
    #     no_empties = ["str1", "str2", "str3"]

    #     assert remove_empties(no_empties) == no_empties  # should output an identical list
    #     assert (
    #         remove_empties(with_empties) == no_empties
    #     )  # should output the predefined no_empties list

    def test_create_gcmd_str(self):
        categories = ['cat1', 'cat2', 'cat3', None, ""]

        assert create_gcmd_str(categories) == 'cat1 > cat2 > cat3'
