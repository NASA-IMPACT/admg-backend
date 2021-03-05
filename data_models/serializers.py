import json
from uuid import uuid4

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import GEOSGeometry
from rest_framework import serializers

from data_models import models


def get_uuids(database_entries):
    return list(database_entries.values_list("uuid", flat=True))


def get_geojson_from_bb(bb_data):
    """
    get a geojson input from the bounding box data

    Args:
        bb_data (string) : comma separated values for bounding box "n, s, e, w" [ (lat/lng) ]

    Returns:
        string : geojson format for the bounding box
    """
    n, s, e, w = [float(coord) for coord in bb_data.split(",")]
    retval = {
        "type": "Polygon",
        "coordinates": [
            [
                [w, s],
                [e, s],
                [e, n],
                [w, n],
                [w, s],
            ]
        ],
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


class BaseSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(default=uuid4)


class GetAliasSerializer(BaseSerializer):
    aliases = serializers.SerializerMethodField(read_only=True)

    def get_aliases(self, obj):
        return get_uuids(obj.aliases)


class GetDoiSerializer(BaseSerializer):
    dois = serializers.SerializerMethodField(read_only=True)

    def get_dois(self, obj):
        return get_uuids(obj.dois)


class ImageSerializer(BaseSerializer):
    class Meta:
        model = models.Image
        fields = "__all__"


class PlatformTypeSerializer(BaseSerializer):
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


class MeasurementTypeSerializer(BaseSerializer):
    instruments = serializers.SerializerMethodField(read_only=True)
    sub_types = serializers.SerializerMethodField(read_only=True)

    def get_instruments(self, obj):
        return get_uuids(obj.instruments)

    def get_sub_types(self, obj):
        return get_uuids(obj.sub_types)

    class Meta:
        model = models.MeasurementType
        fields = "__all__"


class MeasurementStyleSerializer(BaseSerializer):
    instruments = serializers.SerializerMethodField(read_only=True)
    sub_types = serializers.SerializerMethodField(read_only=True)

    def get_instruments(self, obj):
        return get_uuids(obj.instruments)

    def get_sub_types(self, obj):
        return get_uuids(obj.sub_types)

    class Meta:
        model = models.MeasurementStyle
        fields = "__all__"


class HomeBaseSerializer(BaseSerializer):
    class Meta:
        model = models.HomeBase
        fields = "__all__"


class FocusAreaSerializer(BaseSerializer):
    campaigns = serializers.SerializerMethodField(read_only=True)

    def get_campaigns(self, obj):
        return get_uuids(obj.campaigns)

    class Meta:
        model = models.FocusArea
        fields = "__all__"


class SeasonSerializer(BaseSerializer):
    campaigns = serializers.SerializerMethodField(read_only=True)

    def get_campaigns(self, obj):
        return get_uuids(obj.campaigns)

    class Meta:
        model = models.Season
        fields = "__all__"


class RepositorySerializer(BaseSerializer):
    instruments = serializers.SerializerMethodField(read_only=True)
    campaigns = serializers.SerializerMethodField(read_only=True)

    def get_instruments(self, obj):
        return get_uuids(obj.instruments)

    def get_campaigns(self, obj):
        return get_uuids(obj.campaigns)

    class Meta:
        model = models.Repository
        fields = "__all__"


class MeasurementRegionSerializer(BaseSerializer):
    instruments = serializers.SerializerMethodField(read_only=True)

    def get_instruments(self, obj):
        return get_uuids(obj.instruments)

    class Meta:
        model = models.MeasurementRegion
        fields = "__all__"


class GeographicalRegionSerializer(BaseSerializer):
    deployments = serializers.SerializerMethodField(read_only=True)

    def get_deployments(self, obj):
        return get_uuids(obj.deployments)

    class Meta:
        model = models.GeographicalRegion
        fields = "__all__"


class GeophysicalConceptSerializer(BaseSerializer):
    campaigns = serializers.SerializerMethodField(read_only=True)

    def get_campaigns(self, obj):
        return get_uuids(obj.campaigns)

    class Meta:
        model = models.GeophysicalConcept
        fields = "__all__"


class WebsiteTypeSerializer(BaseSerializer):
    websites = serializers.SerializerMethodField(read_only=True)

    def get_websites(self, obj):
        return get_uuids(obj.websites)

    class Meta:
        model = models.WebsiteType
        fields = "__all__"


class PartnerOrgSerializer(GetAliasSerializer):
    campaigns = serializers.SerializerMethodField(read_only=True)

    def get_campaigns(self, obj):
        return get_uuids(obj.campaigns)

    class Meta:
        model = models.PartnerOrg
        fields = "__all__"


class AliasSerializer(BaseSerializer):
    class Meta:
        model = models.Alias
        fields = "__all__"


class GcmdProjectSerializer(BaseSerializer):
    campaigns = serializers.SerializerMethodField(read_only=True)

    def get_campaigns(self, obj):
        return get_uuids(obj.campaigns)

    class Meta:
        model = models.GcmdProject
        fields = "__all__"


class GcmdInstrumentSerializer(BaseSerializer):
    instruments = serializers.SerializerMethodField(read_only=True)

    def get_instruments(self, obj):
        return get_uuids(obj.instruments)

    class Meta:
        model = models.GcmdInstrument
        fields = "__all__"


class GcmdPlatformSerializer(BaseSerializer):
    platforms = serializers.SerializerMethodField(read_only=True)

    def get_platforms(self, obj):
        return get_uuids(obj.platforms)

    class Meta:
        model = models.GcmdPlatform
        fields = "__all__"


class GcmdPhenomenaSerializer(BaseSerializer):
    instruments = serializers.SerializerMethodField(read_only=True)

    def get_instruments(self, obj):
        return get_uuids(obj.instruments)

    class Meta:
        model = models.GcmdPhenomena
        fields = "__all__"


class WebsiteSerializer(BaseSerializer):
    campaigns = serializers.SerializerMethodField(read_only=True)

    def get_campaigns(self, obj):
        return get_uuids(obj.campaigns)

    class Meta:
        model = models.Website
        fields = "__all__"


class DOISerializer(BaseSerializer):
    class Meta:
        model = models.DOI
        fields = "__all__"


class DeploymentSerializer(GetAliasSerializer):
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


class IOPSerializer(BaseSerializer):
    significant_events = serializers.SerializerMethodField(read_only=True)

    def get_significant_events(self, obj):
        return get_uuids(obj.significant_events)

    class Meta:
        model = models.IOP
        fields = "__all__"


class SignificantEventSerializer(BaseSerializer):
    class Meta:
        model = models.SignificantEvent
        fields = "__all__"


class CollectionPeriodSerializer(GetDoiSerializer):
    class Meta:
        model = models.CollectionPeriod
        fields = "__all__"


class PlatformSerializer(GetAliasSerializer, GetDoiSerializer):
    collection_periods = serializers.SerializerMethodField(read_only=True)
    instruments = serializers.ListField(read_only=True)
    campaigns = serializers.ListField(read_only=True)

    def get_collection_periods(self, obj):
        return get_uuids(obj.collection_periods)

    class Meta:
        model = models.Platform
        fields = "__all__"


class InstrumentSerializer(GetAliasSerializer, GetDoiSerializer):
    platforms = serializers.ListField(read_only=True)
    campaigns = serializers.ListField(read_only=True)
    collection_periods = serializers.SerializerMethodField(read_only=True)

    def get_collection_periods(self, obj):
        return get_uuids(obj.collection_periods)

    class Meta:
        model = models.Instrument
        fields = "__all__"


class WebsiteTitleURLRelatedField(serializers.RelatedField):
    """
    A read only field that represents a website using the
    plain string representation of title and URL.
    """

    def __init__(self, **kwargs):
        kwargs["read_only"] = True
        super().__init__(**kwargs)

    def to_representation(self, value):
        return f"{value.url} ({value.title})"


class CampaignWebsiteReadSerializer(BaseSerializer):
    """
    Serializer to read all websites for a given campaign
    """

    website = WebsiteTitleURLRelatedField(read_only=True)

    class Meta:
        model = models.CampaignWebsite
        fields = [
            "website",
            "priority",
        ]


class CampaignWebsiteSerializer(BaseSerializer):
    """
    Serializer specifically for the linking table.
    Can also be used to write data to the linking table directly.
    """

    class Meta:
        model = models.CampaignWebsite
        fields = "__all__"


class CampaignSerializer(GetAliasSerializer, GetDoiSerializer):
    deployments = serializers.SerializerMethodField(read_only=True)
    significant_events = serializers.ListField(read_only=True)
    iops = serializers.ListField(read_only=True)
    number_deployments = serializers.IntegerField(read_only=True)
    instruments = serializers.ListField(read_only=True)
    platforms = serializers.ListField(read_only=True)

    websites = CampaignWebsiteReadSerializer(source="campaignwebsite_set", many=True)

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
