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
from kms.fixtures.gcmd_fixtures import mock_concepts

TEST_FILE_DIRECTORY = "kms/files/"

@pytest.mark.django_db
class TestGCMD():
    @staticmethod
    def open_json_file(filepath):
        return json.load(open(filepath, 'r'))

    @staticmethod
    def open_pickle_file(filepath):
        return pickle.load(open(filepath, 'rb'))

    def test_convert_record(self, convert_record_input, convert_record_result):
        assert gcmd.convert_record(convert_record_input, models.GcmdProject) == convert_record_result

    def test_compare_record_with_concept(self, compare_record_with_concept_row, compare_record_with_concept_dict):
        assert gcmd.compare_record_with_concept(compare_record_with_concept_row, compare_record_with_concept_dict) == True

    def test_delete_old_records(self, delete_old_records_uuids):
        # TODO: Make it so model type is parameter
        gcmd.delete_old_records(delete_old_records_uuids["delete_gcmd_uuids"], models.GcmdInstrument)
        # After deleting, make sure the change records have the correct uuids.
        for uuid in delete_old_records_uuids["change_model_uuids"]:
            assert Change.objects.filter(model_instance_uuid=uuid, action=DELETE).exists()

    def test_check_change_records(self, check_concept, check_action, check_model, check_model_uuid, check_exists):
        row_exists = gcmd.check_change_records(check_concept, check_action, check_model, check_model_uuid) is not None
        assert row_exists == check_exists

    def test_is_valid_concept(self, is_valid_concept, is_valid_model, is_valid_outcome):
        assert gcmd.is_valid_concept(is_valid_concept, is_valid_model) == is_valid_outcome

# @pytest.fixture
# def mock_response(monkeypatch):
#     def mock_list_concepts(*args, **kwargs):
#         return json.load(open(os.path.join(TEST_FILE_DIRECTORY, "list_concepts.json"), 'r'))

#     monkeypatch.setattr(api, "list_concepts", mock_list_concepts)

@pytest.fixture
def mock_list_concepts(*args, **kwargs):
        concepts = json.load(open(os.path.join(TEST_FILE_DIRECTORY, "list_concepts.json"), 'r'))
        return mock.MagicMock(return_value=concepts)


# Try using mock/patch
# @mock.patch.multiple("kms.gcmd", mock_is_valid=mock.MagicMock(return_value=True))
# @mock.patch("kms.api.list_concepts", mock.MagicMock(return_value=mock_list_concepts()))
# def test_sync_gcmd(mock_list_concepts):
#     # mock_object.return_value = json.load(open(os.path.join(TEST_FILE_DIRECTORY, "list_concepts.json"), 'r'))
#     # mock_list_concepts.return_value = mock_list_concepts()
#     tasks.sync_gcmd("platforms")
#     print(f"Assert Called: {mock_list_concepts.call_args_list}")

#     # Python unittest runner version of test above.
#     def test_convert_record(self):
#         test_file_directory = "files/"
#         inputs = ["convert_record_input1.json"]
#         outputs = ["convert_record_output1.json"]

#         for input, output in zip(inputs, outputs):
#             assert self.open_json_file(os.path.join(test_file_directory, input)) == self.open_json_file(os.path.join(test_file_directory, output))