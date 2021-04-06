import json
import logging

from django.contrib.gis.forms import widgets
from django.forms.widgets import Textarea
from data_models.serializers import get_geojson_from_bb
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.gis.geos import GEOSException, GEOSGeometry

logger = logging.getLogger(__name__)


def get_json_representation(value: str):
    try:
        json.loads(value)
        return value
    except json.JSONDecodeError:
        return get_geojson_from_bb(value)


# def get_custom_bbox_representation(value: str):


class BoundingBoxWidget(widgets.OpenLayersWidget):
    map_srid = 3857

    # NOTES: I still have no idea when format_value(), serialize(), and deserialize() are called.
    # It seems like they all get called on every page load...

    # def format_value(self, value):
    #     # return "45, 44, -121, -124"
    #     if isinstance(value, str):
    #         try:
    #             value = GEOSGeometry(value)
    #         except (GEOSException, ValueError):
    #             return value

    #     value.transform(
    #         CoordTransform(SpatialReference(self.map_srid), SpatialReference(4326))
    #     )

    #     return ",".join(
    #         [
    #             max(str(lat) for lat, lng in value.tuple[0]),
    #             min(str(lat) for lat, lng in value.tuple[0]),
    #             max(str(lng) for lat, lng in value.tuple[0]),
    #             min(str(lng) for lat, lng in value.tuple[0]),
    #         ]
    #     )

    # def serialize(self, value):
    #     return super().serialize(value)

    def deserialize(self, value):
        """ Create a geometry object from string """
        try:
            geom = GEOSGeometry(get_json_representation(value))
            if geom.srid != self.map_srid:
                geom.transform(
                    CoordTransform(
                        SpatialReference(geom.srid), SpatialReference(self.map_srid)
                    )
                )
            return geom
        except (GEOSException, ValueError, TypeError) as err:
            logger.error("Error creating geometry from value '%s' (%s)", value, err)
        return None
