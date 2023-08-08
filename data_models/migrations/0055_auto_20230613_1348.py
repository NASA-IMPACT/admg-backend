# Generated by Django 4.1.5 on 2023-06-13 18:48

import ast
import json
import logging
from django.db import migrations

logger = logging.getLogger(__name__)

fields_to_convert = [
    "cmr_projects",
    "cmr_dates",
    "cmr_plats_and_insts",
    "cmr_science_keywords",
    "cmr_data_formats",
]


def convert_cmr_data_to_json(apps, schema_editor):
    DOI = apps.get_model("data_models", "DOI")

    dois = DOI.objects.all()
    for doi in dois:
        for field in fields_to_convert:
            logger.info(f"Converting {field} on {doi.uuid} to JSON")
            d = getattr(doi, field)
            if d is None or d == "":
                logger.info(f"Field {field} is empty, setting to null")
                json_data = None
            else:
                if isinstance(d, str):
                    try:
                        json_data = json.loads(d)
                    except json.decoder.JSONDecodeError:
                        logger.info(
                            f"Failed to parse JSON on {doi.uuid} field {field}, attempting to convert to JSON from serialized python object {d}"
                        )
                        try:
                            if field == "cmr_data_formats" and "[" not in d:
                                d = f'["{d}"]'
                            decoded_string = d.encode("utf-8").decode('unicode_escape')
                            json_data = ast.literal_eval(decoded_string)
                        except Exception as err:
                            logger.error(f"Failed to convert {field} on {doi.uuid} to JSON: {err}")
                            logger.error(f"Value: {decoded_string}")
                            raise err
                else:
                    json_data = d
            setattr(doi, field, json.dumps(json_data))
        doi.save()


class Migration(migrations.Migration):
    dependencies = [
        ('data_models', '0054_remove_instrument_additional_metadata'),
    ]

    operations = [
        migrations.RunPython(convert_cmr_data_to_json, reverse_code=migrations.RunPython.noop)
    ]
