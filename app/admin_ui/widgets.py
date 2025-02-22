import json
import logging
from typing import Optional

from django import forms
from django.conf import settings
from django.contrib.gis import gdal
from django.contrib.gis.forms import widgets
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import GEOSGeometry
from django.urls import reverse
from django.utils import translation
from django.utils.safestring import mark_safe

from api_app.models import Change
from api_app.urls import camel_to_snake
from data_models.models import Image
from data_models.serializers import get_geojson_from_bb

logger = logging.getLogger(__name__)


class BoundingBoxWidget(widgets.OpenLayersWidget):
    template_name = "widgets/custommap.html"
    # This srid is used in the frontend map display
    map_srid = 3857

    @staticmethod
    def get_json_representation(value: str):
        try:
            json.loads(value)
            return value
        except json.JSONDecodeError:
            return get_geojson_from_bb(value)

    def get_context(self, name, value: Optional[GEOSGeometry | str], attrs):
        # Handle blank form
        if not value:
            extent = ''

        # Handle data
        else:
            # Convert string extents (e.g. '39.5, 1.5, -15.0, -50.0') to geometry
            if isinstance(value, str):
                value = GEOSGeometry(self.get_json_representation(value))

            # Get string extents in lat/lng
            W, S, E, N = value.transform(
                CoordTransform(SpatialReference(value.srid), SpatialReference(4326)),
                clone=True,
            ).extent
            extent = f"{N}, {S}, {E}, {W}"

            # Convert geometry to map SRID
            if value.srid != self.map_srid:
                value.transform(
                    CoordTransform(SpatialReference(value.srid), SpatialReference(self.map_srid))
                )

        context = super().get_context(name, value, attrs)
        geom_type = gdal.OGRGeomType(self.attrs["geom_type"]).name
        context.update(
            self.build_attrs(
                self.attrs,
                {
                    "name": name,
                    "module": "geodjango_%s" % name.replace("-", "_"),  # JS-safe
                    "serialized": value.geojson if value else None,
                    "extent": extent,
                    "geom_type": "Geometry" if geom_type == "Unknown" else geom_type,
                    "STATIC_URL": settings.STATIC_URL,
                    "LANGUAGE_BIDI": translation.get_language_bidi(),
                    **(attrs or {}),
                },
            )
        )
        return context


class IconBooleanWidget(forms.NullBooleanSelect):
    template_name = "widgets/icon_radio.html"

    class Media:
        css = {"all": ("css/icon-boolean.css",)}
        js = ("js/icon-boolean.js",)


class ImagePreviewWidget(forms.widgets.FileInput):
    def render(self, name, value, attrs=None, **kwargs):
        value = Image(image=value).image if isinstance(value, str) else value
        input_html = super().render(name, value, attrs=None, **kwargs)
        if value:
            img_html = mark_safe(f'<img class="img-thumbnail" src="{value.url}"/>')
            return f"{img_html}{input_html}"
        else:
            return input_html


class AddAnotherChoiceFieldWidget(forms.Select):
    def __init__(self, model, *args, **kwargs):
        self.model = model
        return super().__init__(*args, **kwargs)

    def render(self, name, value, *args, **kwargs):
        create_form_url = reverse(
            "change-add", kwargs={"model": camel_to_snake(self.model._meta.object_name)}
        )

        output = [
            super().render(name, value, *args, **kwargs),
            f"<a class='add-another small' data-select_id='id_{name}'"
            f" data-form_url='{create_form_url}?_popup=1' href='#'>&plus; Add new"
            f" {self.model._meta.verbose_name.title()}</a>",
        ]
        if value:
            # add a published url if available
            try:
                published = self.model.objects.get(pk=value)
            except self.model.DoesNotExist:
                pass
            else:
                published_url = reverse(
                    "published-detail",
                    kwargs={
                        "canonical_uuid": published.pk,
                        "model": camel_to_snake(self.model._meta.object_name),
                    },
                )
                output.append(
                    f"<a class='link-to small' data-select_id='id_published_{name}'"
                    f" href='{published_url}' target='_blank'>&#x29c9; View published"
                    f" {self.model._meta.verbose_name.title().lower()}</a>"
                )
            # get most recent active draft
            active_draft = (
                Change.objects.filter(model_instance_uuid=value)
                .exclude(status__in=(Change.Statuses.PUBLISHED, Change.Statuses.IN_TRASH))
                .order_by("-updated_at")
                .first()
            )
            if active_draft:
                update_form_url = reverse("change-update", kwargs={"pk": active_draft.pk})
                output.append(
                    f"<a class='link-to small' data-select_id='id_{name}' href='{update_form_url}'"
                    " target='_blank'>&#x29c9; View latest draft</a>"
                )
        return mark_safe("<br>".join(output))

    class Media:
        js = ("js/add-another-choice-field.js", "js/link-to-choice-field.js")
