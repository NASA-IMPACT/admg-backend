import django_tables2 as tables
from api_app.urls import camel_to_snake
from django_tables2 import A


def build_published_table(model_name, link_field):
    class PublishedTable(tables.Table):
        ...

    # TODO: ADD columns specific to the model
    PublishedTable.base_columns[link_field] = tables.Column(
        linkify=(
            f"{camel_to_snake(model_name)}-detail-published",
            [A("uuid")],
        ),
    )

    PublishedTable.__name__ = f"Published{model_name}Table"
    return PublishedTable
