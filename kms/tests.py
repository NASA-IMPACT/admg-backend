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
        gcmd.delete_old_records(delete_old_records_uuids["delete_gcmd_uuids"], models.GcmdInstrument)
        # After deleting, make sure the change records have the correct uuids.
        for uuid in delete_old_records_uuids["change_model_uuids"]:
            assert Change.objects.filter(model_instance_uuid=uuid, action=DELETE).exists()

    def test_get_change(self, get_change_concept, get_change_model, get_change_action, get_change_exists, get_change_model_uuid):
        row_exists = gcmd.get_change(get_change_concept, get_change_model, get_change_action, get_change_model_uuid) is not None
        assert row_exists == get_change_exists

    # TODO: Create a test for updating a change record that is already in database.
    def test_create_change(self, create_change_input):
        before_count = Change.objects.count()
        gcmd.create_change(
            create_change_input["concept"],
            create_change_input["model"],
            create_change_input["action"],
            create_change_input["model_uuid"]
        )
        change = gcmd.get_change(create_change_input["concept"], create_change_input["model"], create_change_input["action"], create_change_input["model_uuid"])
        assert before_count + 1 == Change.objects.count()
        assert change.status == 0
        if create_change_input["action"] == DELETE:
            assert change.update == {}
        else:
            assert change.update == create_change_input["concept"]

    def test_is_valid_concept(self, is_valid_concept, is_valid_model, is_valid_outcome):
        assert gcmd.is_valid_concept(is_valid_concept, is_valid_model) == is_valid_outcome

    # Try using mock/patch
    @mock.patch("kms.gcmd.is_valid_concept", mock.Mock(return_value=True))   # Won't create a mock object!
    @mock.patch("kms.gcmd.delete_old_records")
    @mock.patch("kms.gcmd.create_change")
    #@mock.patch("kms.gcmd.convert_record")
    @mock.patch("kms.api.list_concepts")
    def test_sync_gcmd(self, mock_list_concepts, mock_create_change, mock_delete_old_records):
        mock_list_concepts.return_value=mock_concepts
        #mock_convert_record.side_effect = lambda r,m: del r["UUID"]            # Make side effect the actual function
        tasks.sync_gcmd("sciencekeywords")
        print(f"List Concepts Arg List: {mock_list_concepts.call_args_list}")
        #print(f"Convert Record Arg List: {mock_convert_record.call_args_list}")
        print(f"Create Change Arg List: {mock_create_change.call_args_list}")
        print(f"Create Term Call Length: {len(mock_create_change.call_args_list)}")
        for x, concept in enumerate(mock_concepts):
            args, kwargs = mock_create_change.call_args_list[x]
            if x % 2 == 1:
                assert args[0] == concept
            print(f"Call Type: {mock_create_change.call_args_list[x][0]}")
