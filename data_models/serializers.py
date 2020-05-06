from django.apps import apps
from rest_framework import serializers


class PlatformTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "PlatformType")
        fields = "__all__"



class InstrumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "InstrumentType")
        fields = "__all__"


class HomeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "HomeBase")
        fields = "__all__"


class FocusAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "FocusArea")
        fields = "__all__"


class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "Season")
        fields = "__all__"


class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "Repository")
        fields = "__all__"


class MeasurementRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "MeasurementRegion")
        fields = "__all__"


class MeasurementKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "MeasurementKeyword")
        fields = "__all__"


class GeographicalRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "GeographicalRegion")
        fields = "__all__"


class GeophysicalConceptsSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "GeophysicalConcepts")
        fields = "__all__"


class GcmdPhenomenaSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "GcmdPhenomena")
        fields = "__all__"


class GcmdProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "GcmdProject")
        fields = "__all__"


class GcmdPlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "GcmdPlatform")
        fields = "__all__"


class GcmdInstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "GcmdInstrument")
        fields = "__all__"


class PartnerOrgSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "PartnerOrg")
        fields = "__all__"


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "Campaign")
        fields = "__all__"


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "Platform")
        fields = "__all__"


class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "Instrument")
        fields = "__all__"


class DeploymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "Deployment")
        fields = "__all__"


class IOPSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "IOP")
        fields = "__all__"


class SignificantEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "SignificantEvent")
        fields = "__all__"


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("data_models", "Flight")
        fields = "__all__"
