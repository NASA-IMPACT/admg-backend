from django.forms import model_to_dict
import pytest
import json
import pickle
import os
from unittest import mock
from django.test import TestCase

# TODO: Figure out if this should be "from . import ..." I was having trouble getting it to work with pytest mock.
from kms import gcmd, api, tasks
from data_models import models
from api_app.models import Change, CREATE, UPDATE, DELETE

TEST_FILE_DIRECTORY = "kms/files/"

@pytest.mark.django_db
class TestGCMD():
    @staticmethod
    def open_json_file(filepath):
        return json.load(open(filepath, 'r'))

    @staticmethod
    def open_pickle_file(filepath):
        return pickle.load(open(filepath, 'rb'))

    # @pytest.mark.parametrize("input_file, correct_file", [("convert_record_input1.json", "convert_record_output1.json")])
    # def test_convert_record(self, input_file, correct_file):
    #     input_dict = self.open_json_file(os.path.join(TEST_FILE_DIRECTORY, input_file))
    #     correct_dict = self.open_json_file(os.path.join(TEST_FILE_DIRECTORY, correct_file))

    #     assert gcmd.convert_record(input_dict, models.GcmdProject) == correct_dict

    def test_convert_record(self, convert_record_input, convert_record_result):
        assert gcmd.convert_record(convert_record_input, models.GcmdProject) == convert_record_result

    @pytest.mark.parametrize("row_file, dict_file, outcome", [("row_1", "concept_1.json", True)])
    def test_compare_record_with_concept(self, row_file, dict_file, outcome):
        UNIT_DIRECTORY = "compare_record_with_concept/"
        input_row = self.open_pickle_file(os.path.join(TEST_FILE_DIRECTORY, UNIT_DIRECTORY, row_file))
        input_dict = self.open_json_file(os.path.join(TEST_FILE_DIRECTORY, UNIT_DIRECTORY, dict_file))
        print(f"Input Row: {input_row}")
        assert gcmd.compare_record_with_concept(input_row, input_dict) == outcome

    @pytest.mark.parametrize("uuids_file", [("uuids_1.json")])
    def test_delete_old_records(self, uuids_file):
        UNIT_DIRECTORY = "delete_old_records/"
        uuids = self.open_json_file(os.path.join(TEST_FILE_DIRECTORY, UNIT_DIRECTORY, uuids_file))

        # TODO: Make it so model type is parameter
        gcmd.delete_old_records(uuids["delete_gcmd_uuids"], models.GcmdInstrument)
        # After deleting, make sure the change records have the correct uuids.
        for uuid in uuids["change_model_uuids"]:
            assert Change.objects.filter(model_instance_uuid=uuid, action=DELETE).exists()

    @pytest.mark.parametrize(
        "concept_file, action, model, model_uuid, should_exist",
        [("concept_1.json", CREATE, models.GcmdInstrument, None, True)]
    )
    def test_check_change_records(self, concept_file, action, model, model_uuid, should_exist):
        UNIT_DIRECTORY = "check_change_records/"
        concept = self.open_json_file(os.path.join(TEST_FILE_DIRECTORY, UNIT_DIRECTORY, concept_file))
        row_exists = gcmd.check_change_records(concept, action, model, model_uuid) is not None
        assert row_exists == should_exist

    @pytest.mark.parametrize("record_file,model,outcome",[
        ("project_valid_1.json", models.GcmdProject, True),
        ("project_valid_2.json", models.GcmdProject, True),
        ("project_invalid_1.json", models.GcmdProject, False),
        ("project_invalid_2.json", models.GcmdProject, False),
        ("project_invalid_3.json", models.GcmdProject, False),
        ("project_invalid_4.json", models.GcmdProject, False),
        ("project_invalid_5.json", models.GcmdProject, False),
        ]
    )
    def test_is_valid_concept(self, record_file, model, outcome):
        UNIT_DIRECTORY = "is_valid_concept/"
        record = self.open_json_file(os.path.join(TEST_FILE_DIRECTORY, UNIT_DIRECTORY, record_file))
        assert gcmd.is_valid_concept(record, model) == outcome

# @pytest.fixture
# def mock_response(monkeypatch):
#     def mock_list_concepts(*args, **kwargs):
#         return json.load(open(os.path.join(TEST_FILE_DIRECTORY, "list_concepts.json"), 'r'))

#     monkeypatch.setattr(api, "list_concepts", mock_list_concepts)


def mock_list_concepts(*args, **kwargs):
        return json.load(open(os.path.join(TEST_FILE_DIRECTORY, "list_concepts.json"), 'r'))


# Try using mock/patch
# @mock.patch.multiple("kms.gcmd", mock_is_valid=mock.MagicMock(return_value=True))
# @mock.patch("kms.api.list_concepts", mock_list_concepts)
# def test_sync_gcmd(mock_list_concepts):
#     # mock_object.return_value = json.load(open(os.path.join(TEST_FILE_DIRECTORY, "list_concepts.json"), 'r'))
#     # mock_list_concepts.return_value = mock_list_concepts()   # TODO: Ask Jotham why return_value works but not side_effect.
#     tasks.sync_gcmd("platforms")
#     print(f"Assert Called: {mock_list_concepts.call_args_list}")

#     # Python unittest runner version of test above.
#     def test_convert_record(self):
#         test_file_directory = "files/"
#         inputs = ["convert_record_input1.json"]
#         outputs = ["convert_record_output1.json"]

#         for input, output in zip(inputs, outputs):
#             assert self.open_json_file(os.path.join(test_file_directory, input)) == self.open_json_file(os.path.join(test_file_directory, output))