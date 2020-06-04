import json
from rest_framework import serializers
from django.contrib.gis.geos import GEOSGeometry
from data_models import models

def get_uuids(database_entries):
    return [item.uuid for item in database_entries.all()]

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
    platforms = serializers.SerializerMethodField(read_only=True)
    campaigns = serializers.SerializerMethodField(read_only=True)
    sub_types = serializers.SerializerMethodField(read_only=True)
    
    def get_platforms(self, obj):
        return get_uuids(obj.platforms)

    def get_campaigns(self, obj):
        return get_uuids(obj.campaigns)

    def get_sub_types(self, obj):
        return get_uuids(obj.sub_types)

    class Meta:
        model = models.PlatformType
        fields = "__all__"

class NasaMissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.NasaMission
        fields = "__all__"

class InstrumentTypeSerializer(serializers.ModelSerializer):
    instruments = serializers.SerializerMethodField(read_only=True)
    sub_types = serializers.SerializerMethodField(read_only=True)
    
    def get_instruments(self, obj):
        return get_uuids(obj.instruments)

    def get_sub_types(self, obj):
        return get_uuids(obj.sub_types)

    
    class Meta:
        model = models.InstrumentType
        fields = "__all__"

class HomeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HomeBase
        fields = "__all__"

class FocusAreaSerializer(serializers.ModelSerializer):
    campaigns = serializers.SerializerMethodField(read_only=True)

    def get_campaigns(self, obj):
        return get_uuids(obj.campaigns)

    class Meta:
        model = models.FocusArea
        fields = "__all__"

class SeasonSerializer(serializers.ModelSerializer):
    campaigns = serializers.SerializerMethodField(read_only=True)

    def get_campaigns(self, obj):
        return get_uuids(obj.campaigns)  

    class Meta:
        model = models.Season
        fields = "__all__"

class RepositorySerializer(serializers.ModelSerializer):
    instruments = serializers.SerializerMethodField(read_only=True)
    campaigns = serializers.SerializerMethodField(read_only=True)
    
    def get_instruments(self, obj):
        return get_uuids(obj.instruments)

    def get_campaigns(self, obj):
        return get_uuids(obj.campaigns)


    class Meta:
        model = models.Repository
        fields = "__all__"

class MeasurementRegionSerializer(serializers.ModelSerializer):
    instruments = serializers.SerializerMethodField(read_only=True)
    
    def get_instruments(self, obj):
        return get_uuids(obj.instruments)

    class Meta:
        model = models.MeasurementRegion
        fields = "__all__"

class GeographicalRegionSerializer(serializers.ModelSerializer):
    deployments = serializers.SerializerMethodField(read_only=True)
    
    def get_deployments(self, obj):
        return get_uuids(obj.deployments)

    class Meta:
        model = models.GeographicalRegion
        fields = "__all__"

class GeophysicalConceptSerializer(serializers.ModelSerializer):
    instruments = serializers.SerializerMethodField(read_only=True)
    campaigns = serializers.SerializerMethodField(read_only=True)
    
    def get_instruments(self, obj):
        return get_uuids(obj.instruments)

    def get_campaigns(self, obj):
        return get_uuids(obj.campaigns)

    class Meta:
        model = models.GeophysicalConcept
        fields = "__all__"

class PartnerOrgSerializer(serializers.ModelSerializer):
    campaigns = serializers.SerializerMethodField(read_only=True)

    def get_campaigns(self, obj):
        return get_uuids(obj.campaigns)

    class Meta:
        model = models.PartnerOrg
        fields = "__all__"

class AliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Alias
        fields = "__all__"

class GcmdProjectSerializer(serializers.ModelSerializer):
    campaigns = serializers.SerializerMethodField(read_only=True)

    def get_campaigns(self, obj):
        return get_uuids(obj.campaigns)

    class Meta:
        model = models.GcmdProject
        fields = "__all__"

class GcmdInstrumentSerializer(serializers.ModelSerializer):
    instruments = serializers.SerializerMethodField(read_only=True)

    def get_instruments(self, obj):
        return get_uuids(obj.instruments)

    class Meta:
        model = models.GcmdInstrument
        fields = "__all__"

class GcmdPlatformSerializer(serializers.ModelSerializer):
    platforms = serializers.SerializerMethodField(read_only=True)

    def get_platforms(self, obj):
        return get_uuids(obj.platforms)

    class Meta:
        model = models.GcmdPlatform
        fields = "__all__"

class GcmdPhenomenaSerializer(serializers.ModelSerializer):
    instruments = serializers.SerializerMethodField(read_only=True)
    campaigns = serializers.SerializerMethodField(read_only=True)
    
    def get_instruments(self, obj):
        return get_uuids(obj.instruments)

    def get_campaigns(self, obj):
        return get_uuids(obj.campaigns)

    class Meta:
        model = models.GcmdPhenomena
        fields = "__all__"

class DeploymentSerializer(serializers.ModelSerializer):
    collection_periods = serializers.SerializerMethodField(read_only=True)
    iops = serializers.SerializerMethodField(read_only=True)
    significant_events = serializers.SerializerMethodField(read_only=True)

    def get_significant_events(self, obj):
        return get_uuids(obj.significant_events)

    def get_iops(self, obj):
        return get_uuids(obj.iops)

    def get_collection_periods(self, obj):
        return get_uuids(obj.collection_periods)

    class Meta:
        model = models.Deployment
        fields = "__all__"

class IOPSerializer(serializers.ModelSerializer):
    significant_events = serializers.SerializerMethodField(read_only=True)

    def get_significant_events(self, obj):
        return get_uuids(obj.significant_events)

    class Meta:
        model = models.IOP
        fields = "__all__"

class SignificantEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SignificantEvent
        fields = "__all__"

class CollectionPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CollectionPeriod
        fields = "__all__"

class PlatformSerializer(serializers.ModelSerializer):
    collection_periods = serializers.SerializerMethodField(read_only=True)
    instruments = serializers.ListField(read_only=True)
    campaigns = serializers.ListField(read_only=True)

    def get_collection_periods(self, obj):
        return get_uuids(obj.collection_periods) 

    class Meta:
        model = models.Platform
        fields = "__all__"

class InstrumentSerializer(serializers.ModelSerializer):
    platforms = serializers.ListField(read_only=True)
    campaigns = serializers.ListField(read_only=True)
    collection_periods = serializers.SerializerMethodField(read_only=True)

    def get_collection_periods(self, obj):
        return get_uuids(obj.collection_periods)



    class Meta:
        model = models.Instrument
        fields = "__all__"

class CampaignSerializer(serializers.ModelSerializer):
    deployments = serializers.SerializerMethodField(read_only=True)
    significant_events = serializers.ListField(read_only=True)
    iops = serializers.ListField(read_only=True)
    number_deployments = serializers.IntegerField(read_only=True)
    instruments = serializers.ListField(read_only=True)
    platforms = serializers.ListField(read_only=True)

    def get_deployments(self, obj):
        return get_uuids(obj.deployments)

    def create(self, validated_data):
        validated_data = change_bbox_to_polygon(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data, **kwargs):
        validated_data = change_bbox_to_polygon(validated_data)
        return super().update(instance, validated_data, **kwargs)


    class Meta:
        model = models.Campaign
        fields = "__all__"

class RecommendationSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Recommendation
        fields = "__all__"