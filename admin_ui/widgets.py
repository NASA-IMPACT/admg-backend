import json
import logging

from django import forms
from django.conf import settings
from django.contrib.gis import gdal
from django.contrib.gis.forms import widgets
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.geos import GEOSException, GEOSGeometry
from django.urls import reverse
from django.utils import translation
from django.utils.safestring import mark_safe

from data_models.serializers import get_geojson_from_bb
from data_models.models import Image

logger = logging.getLogger(__name__)


class BoundingBoxWidget(widgets.OpenLayersWidget):
    template_name = "widgets/custommap.html"
    map_srid = 3857

    @staticmethod
    def get_json_representation(value: str):
        try:
            json.loads(value)
            return value
        except json.JSONDecodeError:
            return get_geojson_from_bb(value)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        geom_type = gdal.OGRGeomType(self.attrs["geom_type"]).name
        context.update(
            self.build_attrs(
                self.attrs,
                {
                    "name": name,
                    "module": "geodjango_%s" % name.replace("-", "_"),  # JS-safe
                    "serialized": self.to_geojson(value),
                    "extent": value,
                    "geom_type": "Geometry" if geom_type == "Unknown" else geom_type,
                    "STATIC_URL": settings.STATIC_URL,
                    "LANGUAGE_BIDI": translation.get_language_bidi(),
                    **(attrs or {}),
                },
            )
        )
        return context

    def to_geojson(self, value):
        """ Create a geometry object from string """
        try:
            geom = GEOSGeometry(self.get_json_representation(value))
            if geom.srid != self.map_srid:
                geom.transform(
                    CoordTransform(
                        SpatialReference(geom.srid), SpatialReference(self.map_srid)
                    )
                )
            return geom.json
        except (GEOSException, GDALException, ValueError, TypeError) as err:
            logger.error("Error creating geometry from value '%s' (%s)", value, err)
        return None


class IconBooleanWidget(forms.CheckboxInput):
    template_name = "widgets/icon_radio.html"

    def value_from_datadict(self, data, files, name):
        if name not in data:
            # Unlike a standard checkbox, unspecified data will stay as None and
            # False values must be explicitely sent from browser.
            return None
        return super().value_from_datadict(data, files, name)

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
            "mi-change-add", kwargs={"model": self.model._meta.model_name}
        )

        output = [
            super().render(name, value, *args, **kwargs),
            f"<small class='add-another cursor-pointer' data-select_id='id_{name}' data-form_url='{create_form_url}?_popup=1'>"
            f"&plus; Add new {self.model._meta.verbose_name.title()}"
            "</small>",
        ]
        return mark_safe("".join(output))

    class Media:
        js = ("js/add-another-choice-field.js",)
