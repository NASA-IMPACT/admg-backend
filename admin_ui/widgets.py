import json
import logging

from django import forms
from django.conf import settings
from django.contrib.gis import gdal
from django.contrib.gis.forms import widgets
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.geos import GEOSException, GEOSGeometry
from django.utils import translation

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


class IconBoolean(forms.CheckboxInput):
    template_name = "widgets/icon_radio.html"

    def value_from_datadict(self, data, files, name):
        if name not in data:
            # Unlike a standard checkbox, unspecified data will stay as None and
            # False values must be explicitely sent from browser.
            return None
        return super().value_from_datadict(data, files, name)
