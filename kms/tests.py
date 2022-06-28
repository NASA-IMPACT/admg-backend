from django.forms import model_to_dict
import pytest
from unittest import mock
from copy import deepcopy

from kms import tasks
from data_models import models
from api_app.models import Change
from kms.fixtures.gcmd_fixtures import mock_concepts_changes
from django.contrib.contenttypes.models import ContentType

from kms import gcmd


@pytest.mark.django_db
class TestGCMD:
    @staticmethod
    def get_factory_content_type(factory):
        return ContentType.objects.get_for_model(factory._meta.model)

    @staticmethod
    def make_change_object_from_dict(
        update, content_type, change_action=Change.Actions.CREATE, model_instance_uuid=None
    ):
        if change_action is Change.Actions.CREATE:
            return Change.objects.create(
                content_type=content_type,
                status=Change.Statuses.CREATED,
                action=change_action,
                update=update,
            )
        else:
            return Change.objects.create(
                content_type=content_type,
                status=Change.Statuses.CREATED,
                action=change_action,
                update=update,
                model_instance_uuid=model_instance_uuid,
            )

    @staticmethod
    def make_change_object(factory, change_action=Change.Actions.CREATE) -> Change:
        """make a CREATE change object to use during testing"""
        content_type = TestGCMD.get_factory_content_type(factory)

        return Change.objects.create(
            content_type=content_type,
            status=Change.Statuses.CREATED,
            action=change_action,
            update=factory.as_change_dict(_save=True),
        )

    @pytest.mark.parametrize(
        "concept_input,model_input,concept_output",
        [
            (
                {
                    "Bucket": "A-C",
                    "Short_Name": "Test123",
                    "Long_Name": "LongName123",
                    "UUID": "07a12d76-3794-4d1f-8db3-96a4c9814d54",
                },
                models.GcmdProject,
                {
                    "bucket": "A-C",
                    "short_name": "Test123",
                    "long_name": "LongName123",
                    "gcmd_uuid": "07a12d76-3794-4d1f-8db3-96a4c9814d54",
                },
            )
        ],
    )
    def test_convert_concept(self, concept_input, model_input, concept_output):
        assert gcmd.convert_concept(concept_input, model_input) == concept_output

    @pytest.mark.parametrize("expected_result", [(True), (False)])
    def test_compare_record_with_concept(self, gcmd_factory, expected_result):
        gcmd_object = gcmd_factory.create()
        gcmd_dict = model_to_dict(gcmd_object)
        if not expected_result:
            gcmd_dict["gcmd_uuid"] = "Fake"

        assert gcmd.compare_record_with_concept(gcmd_object, gcmd_dict) == expected_result

    @pytest.mark.parametrize(
        "delete_uuids,change_model_uuids",
        [
            (
                ["16187619-9586-41e3-8faf-16981d5e6ef9", "03c9e37e-d162-43f2-824d-ad4dca88080e"],
                ["eaa1cffc-81d8-4131-a1ba-418a8dfe07e7", "05f36a80-e5b0-4014-96a0-ad6183011da5"],
            )
        ],
    )
    def test_delete_old_records(self, delete_uuids, change_model_uuids):
        gcmd.delete_old_records(delete_uuids, models.GcmdInstrument)
        # After deleting, make sure the change records have the correct uuids.
        for uuid in change_model_uuids:
            assert Change.objects.filter(
                model_instance_uuid=uuid, action=Change.Actions.DELETE
            ).exists()

    # This test and its parameters are all ran once per gcmd keyword type.
    # See gcmd_factory fixture for how the keywords are passed into this test.
    @pytest.mark.parametrize(
        "action,row_exists",
        [
            (Change.Actions.CREATE, True),
            (Change.Actions.UPDATE, True),
            (Change.Actions.DELETE, True),
            (Change.Actions.CREATE, False),
        ],
    )
    def test_get_change(self, gcmd_factory, action, row_exists):
        if row_exists:
            if action is Change.Actions.CREATE:
                change = self.make_change_object(gcmd_factory)
            else:
                # To test a DELETE or UPDATE change record, we need to create an initial published record first.
                gcmd_object = gcmd_factory.create()
                gcmd_dict = model_to_dict(gcmd_object)
                if action is Change.Actions.UPDATE:
                    # Make small change for the update.
                    gcmd_dict["short_name"] = "Test update record"
                elif action is Change.Actions.DELETE:
                    # Delete change is just an empty dictionary for the "update" value in the database.
                    gcmd_dict = {}

                change = self.make_change_object_from_dict(
                    gcmd_dict, self.get_factory_content_type(gcmd_factory), action, gcmd_object.uuid
                )

            change = gcmd.get_change(
                change.update,
                gcmd_factory._meta.model,
                action,
                gcmd_object.uuid if action is not Change.Actions.CREATE else None,
            )

        else:
            # Test trying to get a change that doesn't exist.
            # To do this, create a gcmd record without a change.
            gcmd_object = gcmd_factory.create()
            gcmd_dict = model_to_dict(gcmd_object)
            change = gcmd.get_change(
                gcmd_dict,
                gcmd_factory._meta.model,
                action,
                gcmd_object.uuid if action is not Change.Actions.CREATE else None,
            )

        assert bool(change) is row_exists

    @pytest.mark.parametrize(
        "concept,model,action,model_uuid,new_row",
        [
            (
                {
                    "term": "CALIBRATION/VALIDATION",
                    "category": "EARTH SCIENCE SERVICES",
                    "topic": "DATA ANALYSIS AND VISUALIZATION",
                    "gcmd_uuid": "4f938731-d686-4d89-b72b-ff60474bb1f0",
                },
                models.GcmdPhenomena,
                Change.Actions.CREATE,
                None,
                True,
            ),
            (
                {
                    "term": "ANIMALS/INVERTEBRATES",
                    "category": "EARTH SCIENCE",
                    "topic": "BIOLOGICAL CLASSIFICATION",
                    "variable_1": "MOLLUSKS",
                    "variable_2": "CEPHALOPODS",
                    "variable_3": "OCTOPUS",
                    "gcmd_uuid": "cb21ad9d-7a83-482a-833d-fc3d3079a391",
                },
                models.GcmdPhenomena,
                Change.Actions.UPDATE,
                "31d8bfd0-47db-4260-a0b1-bb632ac629bc",
                True,
            ),
            # Input below reuses Change record already in the database.
            (
                {
                    "short_name": "HALO",
                    "long_name": "High Altitude Lidar Observatory",
                    "instrument_category": "Earth Remote Sensing Instruments",
                    "instrument_class": "Active Remote Sensing",
                    "instrument_type": "Altimeters",
                    "instrument_subtype": "Lidar/Laser Altimeters",
                    "gcmd_uuid": "16187619-9586-41e3-8faf-16981d5e6ef9",
                },
                models.GcmdInstrument,
                Change.Actions.UPDATE,
                "ff6d19df-87c9-42a5-8704-399c65acf2ff",
                False,
            ),
            (
                {"gcmd_uuid": "8c868eeb-b935-4eab-9abf-e6f4dde70fdf"},
                models.GcmdInstrument,
                Change.Actions.DELETE,
                "eaa1cffc-81d8-4131-a1ba-418a8dfe07e7",
                True,
            ),
        ],
    )
    def test_create_change(self, concept, model, action, model_uuid, new_row):
        before_count = Change.objects.count()
        gcmd.create_change(concept, model, action, model_uuid)
        print(f"New Row: {new_row}")
        change = gcmd.get_change(concept, model, action, model_uuid)
        # gcmd.create_change will try to reuse Change records if one exist for the row we are updating.
        # Only check if a new Change row was created if it wasn't supposed to reuse a row (create_change_new_row).
        if new_row:
            assert before_count + 1 == Change.objects.count()
            assert change.status == 0
        else:
            assert before_count == Change.objects.count()

        if action == Change.Actions.DELETE:
            assert change.update == {}
        else:
            assert change.update == concept

    @pytest.mark.parametrize(
        "values,expected_result",
        [
            (("ABC", "CBA", "12345"), True),
            (("not applicable"), False),
            (("ABC", "123"), True),
            (("ABC", "    "), False),
            (("123", "   NOT APPLICABLE"), False),
            ((None, "ABC"), False),
        ],
    )
    def test_is_valid_value(self, values, expected_result):
        assert gcmd.is_valid_value(*values) == expected_result

    @pytest.mark.parametrize(
        "value,expected_result",
        [
            ("ab5250bc-4acd-4624-ac0a-1ba8e54b3d36", True),
            ("ab5250bc-4acd-4624-ac0a-1ba8e54b3d3", False),
            ("b219c209-3d0a-46d3-9ae1-457060f697db", True),
            (None, False),
            ("abc123", False),
        ],
    )
    def test_is_valid_uuid(self, value, expected_result):
        assert gcmd.is_valid_uuid(value) == expected_result

    @pytest.mark.parametrize(
        "concept,model,expected_result",
        [
            (
                {
                    "Bucket": "A-B",
                    "Short_Name": "abc123",
                    "Long_Name": "",
                    "UUID": "80b0db10-fe44-4d15-b66c-374476e8c93b",
                },
                models.GcmdProject,
                True,
            ),
            (
                {
                    "Bucket": "A-Z",
                    "Short_Name": "project123",
                    "Long_Name": "Long Project Name",
                    "UUID": "32ccf67d-e2e1-4fe9-b17d-08bfd6bf1ba3",
                },
                models.GcmdProject,
                True,
            ),
            ({}, models.GcmdProject, False),
            (
                {
                    "Bucket": "A-C",
                    "Short_Name": "",
                    "Long_Name": "Long Project Name",
                    "UUID": "58c2f733-c316-4991-ae9d-d936a75ce365",
                },
                models.GcmdProject,
                False,
            ),
            (
                {
                    "Bucket": "A-C",
                    "Short_Name": "",
                    "Long_Name": "Long Project Name",
                    "UUID": "58c2f733-c316-4991-ae9d-d936a75ce365",
                },
                models.GcmdProject,
                False,
            ),
            (
                {
                    "Bucket": "  NOT APPLICABLE ",
                    "Short_Name": "Project123",
                    "Long_Name": "Long Project Name",
                    "UUID": "58c2f733-c316-4991-ae9d-d936a75ce365",
                },
                models.GcmdProject,
                False,
            ),
            (
                {
                    "Bucket": "A-C",
                    "Short_Name": "Project123",
                    "Long_Name": "Long Project Name",
                    "UUID": "58c2f733-c316-4991-",
                },
                models.GcmdProject,
                False,
            ),
        ],
    )
    def test_is_valid_concept(self, concept, model, expected_result):
        assert gcmd.is_valid_concept(concept, model) == expected_result

    @mock.patch("kms.is_valid_concept", mock.Mock(return_value=True))
    @mock.patch("kms.delete_old_records")
    @mock.patch("kms.create_change")
    @mock.patch("kms.api.list_concepts")
    def test_sync_gcmd(
        self,
        mock_list_concepts,
        mock_create_change,
        mock_delete_old_records,
        sync_gcmd_create_args,
        sync_gcmd_delete_args,
    ):
        mock_list_concepts.return_value = deepcopy(mock_concepts_changes)
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
