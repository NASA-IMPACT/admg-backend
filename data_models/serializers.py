import json
from rest_framework import serializers
from django.contrib.gis.geos import GEOSGeometry
from data_models import models


def get_geojson_from_bb(bb_data):
    """
    get a geojson input from the bounding box data

    Args:
        bb_data (string) : comma separated values for bounding box "n, s, e, w" [ (lat/lng) ]

    Returns:
        string : geojson format for the bounding box
    """
    n, s, e, w = [float(coord) for coord in bb_data.split(',')]
    retval = {
        "type": "Polygon",
        "coordinates": [
            [
                [e, n], [e, s], [w, s], [w, n], [e, n],
            ]
        ]
    }
    return json.dumps(retval)


def change_bbox_to_polygon(validated_data, key="spatial_bounds"):
    """
    change the key to geojson polygon field

    Args:
        validated_data (dict) : the incoming data
        key (string) : the key that is to be changed

    Returns:
        dict : dictionary of the changed validated data
    """
    bb_data = validated_data.get(key)
    if bb_data:
        geojson = get_geojson_from_bb(bb_data)
        polygon = GEOSGeometry(geojson)
        validated_data[key] = polygon
    return validated_data


class PlatformTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PlatformType
        fields = "__all__"


class AircraftTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AircraftType
        fields = "__all__"


class InstrumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InstrumentType
        fields = "__all__"


class HomeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HomeBase
        fields = "__all__"


class FocusAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FocusArea
        fields = "__all__"


class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Season
        fields = "__all__"


class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Repository
        fields = "__all__"


class MeasurementRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MeasurementRegion
        fields = "__all__"


class MeasurementKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MeasurementKeyword
        fields = "__all__"


class GeographicalRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GeographicalRegion
        fields = "__all__"


class GeophysicalConceptsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GeophysicalConcepts
        fields = "__all__"


class GcmdPhenomenaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GcmdPhenomena
        fields = "__all__"


class GcmdProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GcmdProject
        fields = "__all__"


class GcmdPlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GcmdPlatform
        fields = "__all__"


class GcmdInstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GcmdInstrument
        fields = "__all__"


class PartnerOrgSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PartnerOrg
        fields = "__all__"


class CampaignSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        validated_data = change_bbox_to_polygon(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data, **kwargs):
        validated_data = change_bbox_to_polygon(validated_data)
        return super().update(instance, validated_data, **kwargs)

    class Meta:
        model = models.Campaign
        fields = "__all__"


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Platform
        fields = "__all__"


class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Instrument
        fields = "__all__"


class DeploymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Deployment
        fields = "__all__"


class IOPSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IOP
        fields = "__all__"


class SignificantEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SignificantEvent
        fields = "__all__"


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Flight
        fields = "__all__"
