from django.apps import apps
from rest_framework import serializers


class PlatformTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("platform_type", "PlatformType")
        fields = "__all__"

class NasaMissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("nasa_mission", "NasaMission")
        fields = "__all__"

class InstrumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("instrument_type", "InstrumentType")
        fields = "__all__"

class HomeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("home_base", "HomeBase")
        fields = "__all__"

class FocusAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("focus_area", "FocusArea")
        fields = "__all__"

class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("season", "Season")
        fields = "__all__"

class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("repository", "Repository")
        fields = "__all__"

class MeasurementRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("measurement_region", "MeasurementRegion")
        fields = "__all__"

class GeographicalRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("geographical_region", "GeographicalRegion")
        fields = "__all__"

class GeophysicalConceptsSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("geophysical_concepts", "GeophysicalConcepts")
        fields = "__all__"

class PartnerOrgSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("partner_org", "PartnerOrg")
        fields = "__all__"

class AliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("alias", "Alias")
        fields = "__all__"

class GcmdProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("gcmd_project", "GcmdProject")
        fields = "__all__"

class GcmdInstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("gcmd_instrument", "GcmdInstrument")
        fields = "__all__"

class GcmdPlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("gcmd_platform", "GcmdPlatform")
        fields = "__all__"

class GcmdPhenomenaSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("gcmd_phenomena", "GcmdPhenomena")
        fields = "__all__"

class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("campaign", "Campaign")
        fields = "__all__"

class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("platform", "Platform")
        fields = "__all__"

class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("instrument", "Instrument")
        fields = "__all__"

class DeploymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("deployment", "Deployment")
        fields = "__all__"

class IOPSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("iop", "IOP")
        fields = "__all__"

class SignificantEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("significant_event", "SignificantEvent")
        fields = "__all__"

class CollectionPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("collection_period", "CollectionPeriod")
        fields = "__all__"
