import json
import logging

from django import forms
from django.conf import settings
from django.contrib.gis import gdal
from django.contrib.gis.forms import widgets
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.geos import GEOSException, GEOSGeometry, Polygon
from django.urls import reverse
from django.utils import translation
from django.utils.safestring import mark_safe

from data_models.models import Image
from data_models.serializers import get_geojson_from_bb

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
        # this serves the purpose of rendering value saved to models
        # since the code expects a bounding box (comma separated 4 values)
        # we just provide the same kind of input to the code if it is a model value
        if isinstance(value, Polygon):
            W, S, E, N = value.extent
            # show as bounding box
            value = f"{N}, {S}, {E}, {W}"

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
        """Create a geometry object from string"""
        try:
            geom = GEOSGeometry(self.get_json_representation(value))
            if geom.srid != self.map_srid:
                geom.transform(
                    CoordTransform(SpatialReference(geom.srid), SpatialReference(self.map_srid))
                )
            return geom.json
        except (GEOSException, GDALException, ValueError, TypeError) as err:
            logger.error("Error creating geometry from value '%s' (%s)", value, err)
        return None


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
        create_form_url = reverse("change-add", kwargs={"model": self.model._meta.model_name})

        output = [
            super().render(name, value, *args, **kwargs),
            f"<a class='add-another small' data-select_id='id_{name}' data-form_url='{create_form_url}?_popup=1' href='#'>"
            f"&plus; Add new {self.model._meta.verbose_name.title()}"
            "</a>",
        ]
        if value:
            update_form_url = reverse("change-update", kwargs={"pk": value})
            output.append(
                f"<a class='link-to small' data-select_id='id_{name}' href='{update_form_url}' target='_blank'>"
                f"&#x29c9; View selected {self.model._meta.verbose_name.title()}"
                "</a>"
            )
        return mark_safe("<br>".join(output))

    class Media:
        js = ("js/add-another-choice-field.js", "js/link-to-choice-field.js")
