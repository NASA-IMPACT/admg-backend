from django.forms import model_to_dict
import pytest
import json
import pickle
from unittest import mock
from copy import deepcopy

from kms import gcmd, api, tasks
from data_models import models
from api_app.models import Change, CREATE, UPDATE, DELETE
from kms.fixtures.gcmd_fixtures import mock_concepts_changes

@pytest.mark.django_db
class TestGCMD():
    def test_convert_concept(self, convert_concept_input, convert_concept_result):
        assert gcmd.convert_concept(convert_concept_input, models.GcmdProject) == convert_concept_result

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

    def test_create_change(self, create_change_input, create_change_new_row):
        before_count = Change.objects.count()
        gcmd.create_change(
            create_change_input["concept"],
            create_change_input["model"],
            create_change_input["action"],
            create_change_input["model_uuid"]
        )
        print(f"New Row: {create_change_new_row}")
        change = gcmd.get_change(create_change_input["concept"], create_change_input["model"], create_change_input["action"], create_change_input["model_uuid"])
        # gcmd.create_change will try to reuse Change records if one exist for the row we are updating.
        # Only check if a new Change row was created if it wasn't supposed to reuse a row (create_change_new_row).
        if create_change_new_row:
            assert before_count + 1 == Change.objects.count()
            assert change.status == 0
        else:
            assert before_count == Change.objects.count()

        if create_change_input["action"] == DELETE:
            assert change.update == {}
        else:
            assert change.update == create_change_input["concept"]

    @pytest.mark.parametrize("values,expected_result", [
        (("ABC", "123"), True),
        (("ABC", "    "), False),
        (("123", "   NOT APPLICABLE"), False),
        ((None, "ABC"), False)
    ])
    def test_is_valid_value(self, values, expected_result):
        assert gcmd.is_valid_value(*values) == expected_result

    @pytest.mark.parametrize("value,expected_result", [
        ("ab5250bc-4acd-4624-ac0a-1ba8e54b3d36", True),
        ("ab5250bc-4acd-4624-ac0a-1ba8e54b3d3", False),
        ("b219c209-3d0a-46d3-9ae1-457060f697db", True),
        (None, False),
        ("abc123", False)
    ])
    def test_is_valid_uuid(self, value, expected_result):
        assert gcmd.is_valid_uuid(value) == expected_result

    def test_is_valid_concept(self, is_valid_concept, is_valid_model, is_valid_result):
        assert gcmd.is_valid_concept(is_valid_concept, is_valid_model) == is_valid_result

    @mock.patch("kms.gcmd.is_valid_concept", mock.Mock(return_value=True))
    @mock.patch("kms.gcmd.delete_old_records")
    @mock.patch("kms.gcmd.create_change")
    @mock.patch("kms.api.list_concepts")
    def test_sync_gcmd(self, mock_list_concepts, mock_create_change, mock_delete_old_records, sync_gcmd_create_args, sync_gcmd_delete_args):
        mock_list_concepts.return_value=deepcopy(mock_concepts_changes)
        tasks.sync_gcmd("sciencekeywords")

        # Check if arguments passed into create_record are correct.
        call_index = 0
        for concept, expected_args in zip(mock_concepts_changes, sync_gcmd_create_args):
            # create_change() should only be called when there is a change to make.
            # If expected_args is None, then the record should be in database so skip checking.
            if expected_args is not None:
                args, _ = mock_create_change.call_args_list[call_index]
                call_index += 1
                assert args[0] == gcmd.convert_concept(concept, models.GcmdPhenomena)
                assert args[1] == expected_args["model"]
                assert args[2] == expected_args["action"]
                assert args[3] == expected_args["uuid"]
        # Check if create_change() was called the amount of times it should have been.
        assert call_index + 1 == len(mock_create_change.call_args_list)

        # Check if arguments passed into delete_old_records was correct.
        assert len(mock_delete_old_records.call_args_list) == 1
        args, _ = mock_delete_old_records.call_args_list[0]
        assert args[0] == sync_gcmd_delete_args[0]
        assert args[1] == sync_gcmd_delete_args[1]
