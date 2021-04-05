import json
import logging

from django.conf import settings
from django.contrib.gis import gdal
from django.contrib.gis.forms import widgets
from django.forms.widgets import Textarea
from data_models.serializers import get_geojson_from_bb
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.geos import GEOSException, GEOSGeometry
from django.utils import translation

logger = logging.getLogger(__name__)


def get_json_representation(value: str):
    try:
        json.loads(value)
        return value
    except json.JSONDecodeError:
        return get_geojson_from_bb(value)

class BoundingBoxWidget(widgets.OpenLayersWidget):
    template_name = "widgets/custommap.html"

    map_srid = 3857

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        geom_type = gdal.OGRGeomType(self.attrs['geom_type']).name
        context.update(self.build_attrs(self.attrs, {
            'name': name,
            'module': 'geodjango_%s' % name.replace('-', '_'),  # JS-safe
            'serialized': self.to_geojson(value),
            'extent': value,
            'geom_type': 'Geometry' if geom_type == 'Unknown' else geom_type,
            'STATIC_URL': settings.STATIC_URL,
            'LANGUAGE_BIDI': translation.get_language_bidi(),
            **(attrs or {}),
        }))
        return context


    def to_geojson(self, value):
        """ Create a geometry object from string """
        try:
            geom = GEOSGeometry(get_json_representation(value))
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
