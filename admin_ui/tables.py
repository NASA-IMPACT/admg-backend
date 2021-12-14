from uuid import UUID

import django_tables2 as tables
from api_app.models import CREATE, UPDATE, Change
from data_models.models import Campaign, Deployment, Instrument, Platform, Website
from django.urls import reverse
from django_tables2 import A


class ConditionalValueColumn(tables.Column):
    def __init__(self, update_accessor=None, **kwargs):
        super().__init__(**kwargs, empty_values=())
        self.update_accessor = update_accessor

    def _get_processed_value(self, value):
        if value.__class__.__name__ == "ManyRelatedManager":
            many_values = [
                str(uuid) for uuid in list(value.all().values_list("uuid", flat=True))
            ]
            return many_values
        return value

    def get_backup_value(self, **kwargs):
        """Update drafts won't always contain the metadata that
        is needed to be displayed in the table columns. Takes the value
        originally in the row, and if the row is for an UPDATE draft,
        and the value is missing will check the published item to see
        if a value exists.

        Returns:
            value (str): A value which will be displayed in the table
        """

        record = kwargs.get("record")
        value = self._get_processed_value(kwargs.get("value"))

        # This is being called from published tables as well. Which doesn't come with a record with action attribute
        if (
            not value
            and self.update_accessor
            and getattr(record, "action", None) != CREATE
        ):
            accessor = A(self.update_accessor)
            value = self._get_processed_value(accessor.resolve(record))

        return value

    def render(self, **kwargs):
        """Update drafts won't always contain the metadata that
        is needed to be displayed in the table columns. This function
        preferentially displays the draft metadata, and alternately shows
        metadata from the published item if the update draft is empty.

        Returns:
            value (str): A value which will be displayed in the table
        """

        value = self.get_backup_value(**kwargs)

        return value or "---"


class DraftLinkColumn(ConditionalValueColumn):
    def __init__(self, *args, **kwargs):
        self.update_viewname = kwargs.pop("update_viewname", None)
        self.viewname = kwargs.pop("viewname")
        self.url_kwargs = kwargs.pop("url_kwargs")

        super().__init__(*args, **kwargs)

    def get_url(self, **kwargs):
        record = kwargs.get("record")

        url_kwargs = {
            item: getattr(record, self.url_kwargs[item]) for item in self.url_kwargs
        }

        # records from published item do not have action
        if getattr(record, "action", None) == UPDATE:
            view_name = self.update_viewname
        else:
            view_name = self.viewname

        return reverse(view_name, kwargs=url_kwargs)


class ShortNamefromUUIDColumn(ConditionalValueColumn):
    def __init__(self, model=None, **kwargs):
        super().__init__(**kwargs)
        self.model = model

    @staticmethod
    def is_uuid(candidate_uuid):
        """Takes a candidate uuid as a string and returns a boolean
        indicating whether it is a valid UUID.

        Args:
            canndidate_uuid (str): String that might be a UUID

        Returns:
            bool: True if UUID, False if not
        """

        if not isinstance(candidate_uuid, str):
            return False

        try:
            UUID(candidate_uuid, version=4)
            return True
        except ValueError:
            # If it's a value error, then the string
            # is not a valid hex code for a UUID.
            return False

    def get_short_name(self, potential_uuid):

        if not self.is_uuid(potential_uuid) or not self.model:
            return potential_uuid

        try:
            model_object = self.model.objects.get(uuid=potential_uuid)
            return model_object.short_name
        except self.model.DoesNotExist:
            pass

        try:
            change_object = Change.objects.get(uuid=potential_uuid)
            return change_object.update.get("short_name", potential_uuid)
        except Change.DoesNotExist:
            # this really should never happen
            return potential_uuid

    def render(self, **kwargs):
        value = self.get_backup_value(**kwargs)
        if isinstance(value, list):
            return ", ".join(
                self.get_short_name(potential_uuid) for potential_uuid in value
            )
        else:
            return self.get_short_name(value)


class ShortNamefromUUIDLinkColumn(ShortNamefromUUIDColumn, DraftLinkColumn):
    def __init__(self, model=None, **kwargs):
        DraftLinkColumn.__init__(self, **kwargs)
        self.model = model


class DraftTableBase(tables.Table):
    draft_action = tables.Column(verbose_name="Draft Action", accessor="action")
    status = tables.Column(verbose_name="Status", accessor="status")
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")

    final_fields = ("draft_action", "status", "updated_at")

    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped table-responsive",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ("draft_action", "status", "updated_at")
        sequence = ("draft_action", "status", "updated_at")


class LimitedTableBase(DraftTableBase):
    short_name = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name",
        update_accessor="content_object.short_name",
    )
    long_name = ConditionalValueColumn(
        verbose_name="Long name",
        accessor="update__long_name",
        update_accessor="content_object.long_name",
    )

    initial_fields = ("short_name", "long_name")

    class Meta(DraftTableBase.Meta):
        fields = ("short_name", "long_name")
        sequence = ("short_name", "long_name")


class IOPChangeListTable(DraftTableBase):
    short_name = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name",
        update_accessor="content_object.short_name",
    )
    deployment = ShortNamefromUUIDColumn(
        verbose_name="Deployment",
        model=Deployment,
        accessor="update__deployment",
        update_accessor="content_object.deployment",
    )
    start_date = ConditionalValueColumn(
        verbose_name="Start Date",
        accessor="update__start_date",
        update_accessor="content_object.start_date",
    )
    end_date = ConditionalValueColumn(
        verbose_name="End Date",
        accessor="update__end_date",
        update_accessor="content_object.end_date",
    )

    class Meta(DraftTableBase.Meta):
        all_fields = (
            "short_name",
            "deployment",
            "start_date",
            "end_date",
        ) + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class SignificantEventChangeListTable(DraftTableBase):
    short_name = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name",
        update_accessor="content_object.short_name",
    )
    deployment = ShortNamefromUUIDColumn(
        verbose_name="Deployment",
        model=Deployment,
        accessor="update__deployment",
        update_accessor="content_object.deployment",
    )
    start_date = ConditionalValueColumn(
        verbose_name="Start Date",
        accessor="update__start_date",
        update_accessor="content_object.start_date",
    )
    end_date = ConditionalValueColumn(
        verbose_name="End Date",
        accessor="update__end_date",
        update_accessor="content_object.end_date",
    )

    class Meta(DraftTableBase.Meta):
        all_fields = (
            "short_name",
            "deployment",
            "start_date",
            "end_date",
        ) + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class CollectionPeriodChangeListTable(DraftTableBase):
    # TODO: have a calculated short_name field?
    deployment = ShortNamefromUUIDLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={"pk": "uuid"},
        model=Deployment,
        verbose_name="Deployment",
        accessor="update__deployment",
        update_accessor="content_object.deployment",
    )

    platform = ShortNamefromUUIDColumn(
        verbose_name="Platform",
        model=Platform,
        accessor="update__platform",
        update_accessor="content_object.platform",
    )
    instruments = ShortNamefromUUIDColumn(
        verbose_name="Instruments",
        model=Instrument,
        accessor="update__instruments",
        update_accessor="content_object.instruments",
    )

    class Meta(DraftTableBase.Meta):
        all_fields = (
            "deployment",
            "platform",
            "instruments",
        ) + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class DOIChangeListTable(DraftTableBase):
    concept_id = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={"pk": "uuid"},
        verbose_name="Concept ID",
        accessor="update__concept_id",
        update_accessor="content_object.concept_id",
    )
    long_name = ConditionalValueColumn(
        verbose_name="Long Name",
        accessor="update__long_name",
        update_accessor="content_object.long_name",
    )
    campaigns = ShortNamefromUUIDColumn(
        verbose_name="Campaigns",
        model=Campaign,
        accessor="update__campaigns",
        update_accessor="content_object.campaigns",
    )
    platforms = ShortNamefromUUIDColumn(
        verbose_name="Platforms",
        model=Platform,
        accessor="update__platforms",
        update_accessor="content_object.platforms",
    )
    instruments = ShortNamefromUUIDColumn(
        verbose_name="Instruments",
        model=Instrument,
        accessor="update__instruments",
        update_accessor="content_object.instruments",
    )

    class Meta(DraftTableBase.Meta):
        all_fields = (
            "concept_id",
            "long_name",
            "campaigns",
            "platforms",
            "instruments",
        ) + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class DeploymentChangeListTable(LimitedTableBase):

    campaign = ShortNamefromUUIDColumn(
        verbose_name="Campaign",
        model=Campaign,
        accessor="update__campaign",
        update_accessor="content_object.campaign",
    )
    start_date = ConditionalValueColumn(
        verbose_name="Start Date",
        accessor="update__start_date",
        update_accessor="content_object.start_date",
    )
    end_date = ConditionalValueColumn(
        verbose_name="End Date",
        accessor="update__end_date",
        update_accessor="content_object.end_date",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            LimitedTableBase.initial_fields
            + (
                "campaign",
                "start_date",
                "end_date",
            )
            + LimitedTableBase.final_fields
        )
        fields = list(all_fields)
        sequence = all_fields


class PlatformTypeChangeListTable(LimitedTableBase):

    parent = ConditionalValueColumn(
        verbose_name="Parent",
        accessor="update__parent",
        update_accessor="content_object.parent",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            LimitedTableBase.initial_fields
            + ("parent",)
            + LimitedTableBase.final_fields
        )
        fields = list(all_fields)
        sequence = all_fields


class MeasurementTypeChangeListTable(LimitedTableBase):
    parent = ConditionalValueColumn(
        verbose_name="Parent",
        accessor="update__parent",
        update_accessor="content_object.parent",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            LimitedTableBase.initial_fields
            + ("parent",)
            + LimitedTableBase.final_fields
        )
        fields = all_fields
        sequence = all_fields


class MeasurementStyleChangeListTable(LimitedTableBase):
    parent = ConditionalValueColumn(
        verbose_name="Parent",
        accessor="update__parent",
        update_accessor="content_object.parent",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            LimitedTableBase.initial_fields
            + ("parent",)
            + LimitedTableBase.final_fields
        )
        fields = all_fields
        sequence = all_fields


class HomeBaseChangeListTable(LimitedTableBase):
    location = ConditionalValueColumn(
        verbose_name="Location",
        accessor="update__location",
        update_accessor="content_object.location",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            LimitedTableBase.initial_fields
            + ("location",)
            + LimitedTableBase.final_fields
        )
        fields = all_fields
        sequence = all_fields


class FocusAreaChangeListTable(LimitedTableBase):
    url = ConditionalValueColumn(
        verbose_name="Url", accessor="update__url", update_accessor="content_object.url"
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            LimitedTableBase.initial_fields + ("url",) + LimitedTableBase.final_fields
        )
        fields = all_fields
        sequence = all_fields


class SeasonChangeListTable(LimitedTableBase):
    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class RepositoryChangeListTable(LimitedTableBase):
    gcmd_uuid = ConditionalValueColumn(
        verbose_name="GCMD UUID",
        accessor="update__gcmd_uuid",
        update_accessor="content_object.gcmd_uuid",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            LimitedTableBase.initial_fields
            + ("gcmd_uuid",)
            + LimitedTableBase.final_fields
        )
        fields = all_fields
        sequence = all_fields


class MeasurementRegionChangeListTable(LimitedTableBase):
    example = ConditionalValueColumn(
        verbose_name="Example",
        accessor="update__example",
        update_accessor="content_object.example",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            LimitedTableBase.initial_fields
            + ("example",)
            + LimitedTableBase.final_fields
        )
        fields = all_fields
        sequence = all_fields


class GeographicalRegionChangeListTable(LimitedTableBase):
    example = ConditionalValueColumn(
        verbose_name="Example",
        accessor="update__example",
        update_accessor="content_object.example",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            LimitedTableBase.initial_fields
            + ("example",)
            + LimitedTableBase.final_fields
        )
        fields = all_fields
        sequence = all_fields


class GeophysicalConceptChangeListTable(LimitedTableBase):
    example = ConditionalValueColumn(
        verbose_name="Example",
        accessor="update__example",
        update_accessor="content_object.example",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            LimitedTableBase.initial_fields
            + ("example",)
            + LimitedTableBase.final_fields
        )
        fields = all_fields
        sequence = all_fields


class PartnerOrgChangeListTable(LimitedTableBase):
    website = ConditionalValueColumn(
        verbose_name="Website",
        accessor="update__website",
        update_accessor="content_object.website",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            LimitedTableBase.initial_fields
            + ("website",)
            + LimitedTableBase.final_fields
        )
        fields = all_fields
        sequence = all_fields


class WebsiteTypeChangeListTable(LimitedTableBase):
    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class CampaignChangeListTable(LimitedTableBase):
    short_name = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="campaign-detail",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name",
        update_accessor="content_object.short_name",
    )
    funding_agency = ConditionalValueColumn(
        verbose_name="Funding Agency",
        accessor="update__funding_agency",
        update_accessor="content_object.funding_agency",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            LimitedTableBase.initial_fields
            + ("funding_agency",)
            + LimitedTableBase.final_fields
        )
        fields = all_fields
        sequence = all_fields


class PlatformChangeListTable(LimitedTableBase):
    platform_type = ConditionalValueColumn(
        verbose_name="Platform Type",
        accessor="platform_type_name",
        update_accessor="content_object.platform_type",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            LimitedTableBase.initial_fields
            + ("platform_type",)
            + LimitedTableBase.final_fields
        )
        fields = all_fields
        sequence = all_fields


class InstrumentChangeListTable(LimitedTableBase):
    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


# TODO: does this actually need to link to the campaign detail page?
class ChangeSummaryTable(DraftTableBase):
    short_name = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name",
        update_accessor="content_object.short_name",
    )
    content_type__model = tables.Column(
        verbose_name="Model Type", accessor="model_name", order_by="content_type__model"
    )
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date")
    status = tables.Column(verbose_name="Status", accessor="status")

    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped",
            "thead": {"class": "table-primary"},
        }
        fields = ["short_name", "content_type__model", "updated_at", "status"]


class WebsiteChangeListTable(DraftTableBase):
    title = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={"pk": "uuid"},
        verbose_name="Title",
        accessor="update__title",
        update_accessor="content_object.title",
    )
    url = ConditionalValueColumn(
        verbose_name="URL", accessor="update__url", update_accessor="content_object.url"
    )
    website_type = ConditionalValueColumn(
        verbose_name="Website Type",
        accessor="website_type_name",
        update_accessor="content_object.type_name",
    )

    class Meta(DraftTableBase.Meta):
        all_fields = (
            "title",
            "url",
            "website_type",
        ) + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class AliasChangeListTable(DraftTableBase):
    short_name = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name",
        update_accessor="content_object.short_name",
    )
    # TODO replace model_type which short_name of related object
    model_type = ConditionalValueColumn(
        verbose_name="Item Type",
        accessor="update__model_name",
        update_accessor="content_object.model_name",
    )

    class Meta(DraftTableBase.Meta):
        all_fields = (
            "short_name",
            "model_type",
        ) + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class GcmdProjectChangeListTable(DraftTableBase):
    short_name = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name",
        update_accessor="content_object.short_name",
    )
    long_name = ConditionalValueColumn(
        verbose_name="Long Name",
        accessor="update__long_name",
        update_accessor="content_object.long_name",
    )
    bucket = ConditionalValueColumn(
        verbose_name="Bucket",
        accessor="update__bucket",
        update_accessor="content_object.bucket",
    )

    class Meta(DraftTableBase.Meta):
        all_fields = (
            "short_name",
            "long_name",
            "bucket",
        ) + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class GcmdInstrumentChangeListTable(DraftTableBase):
    short_name = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name",
        update_accessor="content_object.short_name",
    )
    long_name = ConditionalValueColumn(
        verbose_name="Long Name",
        accessor="update__long_name",
        update_accessor="content_object.long_name",
    )
    instrument_category = ConditionalValueColumn(
        verbose_name="Instrument Category",
        accessor="update__instrument_category",
        update_accessor="content_object.instrument_category",
    )
    instrument_class = ConditionalValueColumn(
        verbose_name="Instrument Class",
        accessor="update__instrument_class",
        update_accessor="content_object.instrument_class",
    )
    instrument_type = ConditionalValueColumn(
        verbose_name="Instrument Type",
        accessor="update__instrument_type",
        update_accessor="content_object.instrument_type",
    )
    instrument_subtype = ConditionalValueColumn(
        verbose_name="Instrument Subtype",
        accessor="update__instrument_subtype",
        update_accessor="content_object.instrument_subtype",
    )

    class Meta(DraftTableBase.Meta):
        all_fields = (
            "short_name",
            "long_name",
            "instrument_category",
            "instrument_class",
            "instrument_type",
            "instrument_subtype",
        ) + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class GcmdPlatformChangeListTable(DraftTableBase):
    short_name = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={"pk": "uuid"},
        verbose_name="Short Name",
        accessor="update__short_name",
        update_accessor="content_object.short_name",
    )
    long_name = ConditionalValueColumn(
        verbose_name="Long Name",
        accessor="update__long_name",
        update_accessor="content_object.long_name",
    )
    category = ConditionalValueColumn(
        verbose_name="Category",
        accessor="update__category",
        update_accessor="content_object.category",
    )

    class Meta(DraftTableBase.Meta):
        all_fields = (
            "short_name",
            "long_name",
            "category",
        ) + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class GcmdPhenomenaChangeListTable(DraftTableBase):
    variable_3 = DraftLinkColumn(
        update_viewname="change-diff",
        viewname="change-update",
        url_kwargs={"pk": "uuid"},
        verbose_name="Variable 3",
        accessor="update__variable_3",
        update_accessor="content_object.variable_3",
    )
    variable_2 = ConditionalValueColumn(
        verbose_name="Variable 2",
        accessor="update__variable_2",
        update_accessor="content_object.variable_2",
    )
    variable_1 = ConditionalValueColumn(
        verbose_name="Variable 1",
        accessor="update__variable_1",
        update_accessor="content_object.variable_1",
    )
    term = ConditionalValueColumn(
        verbose_name="Term",
        accessor="update__term",
        update_accessor="content_object.term",
    )
    topic = ConditionalValueColumn(
        verbose_name="Topic",
        accessor="update__topic",
        update_accessor="content_object.topic",
    )
    category = ConditionalValueColumn(
        verbose_name="Category",
        accessor="update__category",
        update_accessor="content_object.category",
    )

    class Meta(DraftTableBase.Meta):
        all_fields = (
            "variable_3",
            "variable_2",
            "variable_1",
            "term",
            "topic",
            "category",
        ) + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields
