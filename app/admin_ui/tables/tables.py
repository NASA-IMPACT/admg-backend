from uuid import UUID

from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django_tables2 import A
import django_tables2 as tables
from api_app.urls import camel_to_snake

from api_app.models import Change
from data_models.models import (
    Campaign,
    Deployment,
    Instrument,
    Platform,
    WebsiteType,
)
from api_app.models import ApprovalLog
from admin_ui.utils import get_draft_status_class


class BackupValueColumn(tables.Column):
    """
    Attempt to retrieve a value from a record. If that value is not available (ie is None),
    attempt to retrieve the value from a backup location.
    """

    def __init__(self, backup_accessor=None, **kwargs):
        super().__init__(**kwargs, empty_values=())
        self.backup_accessor = backup_accessor

    def _get_processed_value(self, value):
        if value.__class__.__name__ == "ManyRelatedManager":
            many_values = [str(uuid) for uuid in list(value.all().values_list("uuid", flat=True))]
            return many_values
        return value

    def render(self, *, record, value, **kwargs):
        """Update drafts won't always contain the metadata that
        is needed to be displayed in the table columns. This function
        preferentially displays the accessor metadata, and alternately shows
        metadata from the backup location if the value at the primary accessor is empty.

        Returns:
            value (str): A value which will be displayed in the table
        """
        if value is None or value == '':
            value = A(self.backup_accessor).resolve(record)

        return self._get_processed_value(value) or "---"


class ShortNamefromUUIDColumn(BackupValueColumn):
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

    def get_short_names(self, potential_uuids):
        short_names = {}
        lookup_uuids = []
        for potential_uuid in potential_uuids:
            if not self.is_uuid(potential_uuid):
                short_names[str(potential_uuid)] = potential_uuid
                continue
            else:
                lookup_uuids.append(str(potential_uuid))
        if lookup_uuids:
            model_objects = self.model.objects.filter(uuid__in=lookup_uuids)
            short_names.update(
                {str(model_object.uuid): model_object.short_name for model_object in model_objects}
            )
            missing_uuids = set(lookup_uuids) - set(short_names.keys())
            if missing_uuids:
                change_objects = Change.objects.filter(uuid__in=missing_uuids)
                short_names.update(
                    {
                        str(change_object.uuid): change_object.update.get(
                            "short_name", change_object.uuid
                        )
                        for change_object in change_objects
                    }
                )
        return [short_names[str(potential_uuid)] for potential_uuid in potential_uuids]

    def render(self, **kwargs):
        value = super().render(**kwargs)
        if isinstance(value, list):
            return ", ".join(self.get_short_names(value))
        else:
            return self.get_short_name(value)


class DraftTableBase(tables.Table):
    status = tables.Column(verbose_name="Status", accessor="latest_status")
    last_published = tables.DateTimeColumn(
        verbose_name="Last Published", accessor="latest_published_at"
    )
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date", accessor="latest_updated_at")

    final_fields = ("status", "last_published", "updated_at")

    class Meta:
        model = Change
        attrs = {
            "class": "table table-striped table-responsive",
            "thead": {"class": "table-primary"},
            "th": {"style": "min-width: 10em"},
        }
        fields = ("status", "updated_at")
        sequence = ("status", "updated_at")

    def render_status(self, value, record):
        css_class = get_draft_status_class(value)
        return mark_safe(
            f'<div class="badge badge-pill text-white {css_class}">'
            + record.__class__(status=value).get_status_display()
            + '</div>'
        )


class LimitedTableBase(DraftTableBase):
    short_name = BackupValueColumn(
        verbose_name="Short Name",
        accessor="update__short_name",
        backup_accessor="content_object.short_name",
        linkify=("change-update", [tables.A("uuid")]),
    )
    long_name = BackupValueColumn(
        verbose_name="Long Name",
        accessor="latest_update__long_name",
        backup_accessor="content_object.long_name",
    )

    initial_fields = ("short_name", "long_name")

    class Meta(DraftTableBase.Meta):
        fields = ("short_name", "long_name")
        sequence = ("short_name", "long_name")


class IOPChangeListTable(DraftTableBase):
    short_name = BackupValueColumn(
        verbose_name="Short Name",
        accessor="update__short_name",
        backup_accessor="content_object.short_name",
        linkify=("change-update", [tables.A("uuid")]),
    )
    deployment = ShortNamefromUUIDColumn(
        verbose_name="Deployment",
        model=Deployment,
        accessor="update__deployment",
        backup_accessor="content_object.deployment",
    )
    start_date = BackupValueColumn(
        verbose_name="Start Date",
        accessor="update__start_date",
        backup_accessor="content_object.start_date",
    )
    end_date = BackupValueColumn(
        verbose_name="End Date",
        accessor="update__end_date",
        backup_accessor="content_object.end_date",
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
    short_name = BackupValueColumn(
        verbose_name="Short Name",
        accessor="update__short_name",
        backup_accessor="content_object.short_name",
        linkify=("change-update", [tables.A("uuid")]),
    )
    deployment = ShortNamefromUUIDColumn(
        verbose_name="Deployment",
        model=Deployment,
        accessor="update__deployment",
        backup_accessor="content_object.deployment",
    )
    start_date = BackupValueColumn(
        verbose_name="Start Date",
        accessor="update__start_date",
        backup_accessor="content_object.start_date",
    )
    end_date = BackupValueColumn(
        verbose_name="End Date",
        accessor="update__end_date",
        backup_accessor="content_object.end_date",
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
    deployment = ShortNamefromUUIDColumn(
        linkify=("change-update", [A('uuid')]),
        model=Deployment,
        verbose_name="Deployment",
        accessor="update__deployment",
        backup_accessor="content_object.deployment",
    )

    platform = ShortNamefromUUIDColumn(
        verbose_name="Platform",
        model=Platform,
        accessor="update__platform",
        backup_accessor="content_object.platform",
    )
    instruments = ShortNamefromUUIDColumn(
        verbose_name="Instruments",
        model=Instrument,
        accessor="update__instruments",
        backup_accessor="content_object.instruments",
    )

    class Meta(DraftTableBase.Meta):
        all_fields = ("deployment", "platform", "instruments") + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class DOIChangeListTable(DraftTableBase):
    concept_id = BackupValueColumn(
        verbose_name="Concept ID",
        accessor="update__concept_id",
        backup_accessor="content_object.concept_id",
        linkify=("change-update", [tables.A("uuid")]),
    )
    long_name = BackupValueColumn(
        verbose_name="Long Name",
        accessor="update__long_name",
        backup_accessor="content_object.long_name",
    )
    campaigns = ShortNamefromUUIDColumn(
        verbose_name="Campaigns",
        model=Campaign,
        accessor="update__campaigns",
        backup_accessor="content_object.campaigns",
    )
    platforms = ShortNamefromUUIDColumn(
        verbose_name="Platforms",
        model=Platform,
        accessor="update__platforms",
        backup_accessor="content_object.platforms",
    )
    instruments = ShortNamefromUUIDColumn(
        verbose_name="Instruments",
        model=Instrument,
        accessor="update__instruments",
        backup_accessor="content_object.instruments",
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
        backup_accessor="content_object.campaign",
    )
    start_date = BackupValueColumn(
        verbose_name="Start Date",
        accessor="update__start_date",
        backup_accessor="content_object.start_date",
    )
    end_date = BackupValueColumn(
        verbose_name="End Date",
        accessor="update__end_date",
        backup_accessor="content_object.end_date",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            LimitedTableBase.initial_fields
            + ("campaign", "start_date", "end_date")
            + LimitedTableBase.final_fields
        )
        fields = list(all_fields)
        sequence = all_fields


class PlatformTypeChangeListTable(LimitedTableBase):
    parent = BackupValueColumn(
        verbose_name="Parent", accessor="update__parent", backup_accessor="content_object.parent"
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("parent",) + LimitedTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class MeasurementTypeChangeListTable(LimitedTableBase):
    parent = BackupValueColumn(
        verbose_name="Parent", accessor="update__parent", backup_accessor="content_object.parent"
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("parent",) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class MeasurementStyleChangeListTable(LimitedTableBase):
    parent = BackupValueColumn(
        verbose_name="Parent", accessor="update__parent", backup_accessor="content_object.parent"
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("parent",) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class HomeBaseChangeListTable(LimitedTableBase):
    location = BackupValueColumn(
        verbose_name="Location",
        accessor="update__location",
        backup_accessor="content_object.location",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("location",) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class FocusAreaChangeListTable(LimitedTableBase):
    url = BackupValueColumn(
        verbose_name="Url", accessor="update__url", backup_accessor="content_object.url"
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("url",) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class SeasonChangeListTable(LimitedTableBase):
    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class RepositoryChangeListTable(LimitedTableBase):
    gcmd_uuid = BackupValueColumn(
        verbose_name="GCMD UUID",
        accessor="update__gcmd_uuid",
        backup_accessor="content_object.gcmd_uuid",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            LimitedTableBase.initial_fields + ("gcmd_uuid",) + LimitedTableBase.final_fields
        )
        fields = all_fields
        sequence = all_fields


class MeasurementRegionChangeListTable(LimitedTableBase):
    example = BackupValueColumn(
        verbose_name="Example", accessor="update__example", backup_accessor="content_object.example"
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("example",) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class GeographicalRegionChangeListTable(LimitedTableBase):
    example = BackupValueColumn(
        verbose_name="Example", accessor="update__example", backup_accessor="content_object.example"
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("example",) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class GeophysicalConceptChangeListTable(LimitedTableBase):
    example = BackupValueColumn(
        verbose_name="Example", accessor="update__example", backup_accessor="content_object.example"
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("example",) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class PartnerOrgChangeListTable(LimitedTableBase):
    website = BackupValueColumn(
        verbose_name="Website", accessor="update__website", backup_accessor="content_object.website"
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + ("website",) + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields

    def render_short_name(self, value, record):
        return format_html(
            '<a href="{form_url}">{label}</a>',
            form_url=reverse(
                'canonical-redirect',
                kwargs={
                    "canonical_uuid": record.uuid,
                    "model": camel_to_snake(record.model_name),
                },
            ),
            label=record.update.get('short_name') or '---',
        )


class WebsiteTypeChangeListTable(LimitedTableBase):
    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields


class CampaignChangeListTable(LimitedTableBase):
    short_name = BackupValueColumn(
        verbose_name="Short Name",
        accessor="latest_update__short_name",
        backup_accessor="content_object.short_name",
        linkify=(
            "canonical-redirect",
            {
                "canonical_uuid": tables.A('uuid'),
                "model": 'campaign',
            },
        ),
    )
    funding_agency = BackupValueColumn(
        verbose_name="Funding Agency",
        accessor="latest_update__funding_agency",
        backup_accessor="content_object.funding_agency",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            *LimitedTableBase.initial_fields,
            "funding_agency",
            *LimitedTableBase.final_fields,
        )
        fields = all_fields
        sequence = all_fields


class PlatformChangeListTable(LimitedTableBase):
    platform_type = BackupValueColumn(
        verbose_name="Platform Type",
        accessor="platform_type_name",
        backup_accessor="content_object.platform_type",
    )

    class Meta(LimitedTableBase.Meta):
        all_fields = (
            LimitedTableBase.initial_fields + ("platform_type",) + LimitedTableBase.final_fields
        )
        fields = all_fields
        sequence = all_fields

    def render_short_name(self, value, record):
        return format_html(
            '<a href="{form_url}">{label}</a>',
            form_url=reverse(
                'canonical-redirect',
                kwargs={
                    "canonical_uuid": record.uuid,
                    "model": camel_to_snake(record.model_name),
                },
            ),
            label=record.update.get('short_name') or '---',
        )


class InstrumentChangeListTable(LimitedTableBase):
    class Meta(LimitedTableBase.Meta):
        all_fields = LimitedTableBase.initial_fields + LimitedTableBase.final_fields
        fields = all_fields
        sequence = all_fields

    def render_short_name(self, value, record):
        return format_html(
            '<a href="{form_url}">{label}</a>',
            form_url=reverse(
                'canonical-redirect',
                kwargs={
                    "canonical_uuid": record.uuid,
                    "model": camel_to_snake(record.model_name),
                },
            ),
            label=record.update.get('short_name') or '---',
        )


# TODO: does this actually need to link to the campaign detail page?
class ChangeSummaryTable(DraftTableBase):
    short_name = BackupValueColumn(
        verbose_name="Short Name",
        accessor="update__short_name",
        backup_accessor="content_object.short_name",
        linkify=("change-update", [tables.A("uuid")]),
    )
    content_type__model = tables.Column(
        verbose_name="Model Type", accessor="model_name", order_by="content_type__model"
    )
    status = tables.Column(verbose_name="Status", accessor="latest_status")
    updated_at = tables.DateTimeColumn(verbose_name="Last Edit Date", accessor="updated_at")
    last_published = tables.DateTimeColumn(
        verbose_name="Last Published", accessor="latest_published_at"
    )

    def render_short_name(self, value, record):
        return format_html(
            '<a href="{form_url}" class="draft-link">{label}</a>',
            form_url=reverse(
                'canonical-redirect',
                kwargs={
                    "canonical_uuid": record.model_instance_uuid or record.uuid,
                    "model": camel_to_snake(record.model_name),
                },
            ),
            label=record.update.get('short_name') or '---',
        )

    class Meta:
        model = Change
        attrs = {"class": "table table-striped", "thead": {"class": "table-primary"}}
        fields = ["short_name", "content_type__model", "status", "updated_at", "last_published"]


class WebsiteChangeListTable(DraftTableBase):
    title = BackupValueColumn(
        verbose_name="Title",
        accessor="update__title",
        backup_accessor="content_object.title",
        linkify=("change-update", [tables.A("uuid")]),
    )
    url = BackupValueColumn(
        verbose_name="URL", accessor="update__url", backup_accessor="content_object.url"
    )
    website_type = ShortNamefromUUIDColumn(
        verbose_name="Website Type",
        model=WebsiteType,
        accessor="update__website_type",
        backup_accessor="content_object.website_type",
    )

    class Meta(DraftTableBase.Meta):
        all_fields = ("title", "url", "website_type") + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class AliasChangeListTable(DraftTableBase):
    short_name = BackupValueColumn(
        verbose_name="Short Name",
        accessor="update__short_name",
        backup_accessor="content_object.short_name",
        linkify=("change-update", [tables.A("uuid")]),
    )
    # TODO replace model_type which short_name of related object
    model_type = BackupValueColumn(
        verbose_name="Item Type",
        accessor="update__model_name",
        backup_accessor="content_object.model_name",
    )

    class Meta(DraftTableBase.Meta):
        all_fields = ("short_name", "model_type") + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class GcmdProjectChangeListTable(DraftTableBase):
    short_name = BackupValueColumn(
        verbose_name="Short Name",
        accessor="update__short_name",
        backup_accessor="content_object.short_name",
        linkify=("change-update", [tables.A("uuid")]),
    )
    long_name = BackupValueColumn(
        verbose_name="Long Name",
        accessor="update__long_name",
        backup_accessor="content_object.long_name",
    )
    bucket = BackupValueColumn(
        verbose_name="Bucket", accessor="update__bucket", backup_accessor="content_object.bucket"
    )

    class Meta(DraftTableBase.Meta):
        all_fields = ("short_name", "long_name", "bucket") + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class GcmdInstrumentChangeListTable(DraftTableBase):
    short_name = BackupValueColumn(
        verbose_name="Short Name",
        accessor="update__short_name",
        backup_accessor="content_object.short_name",
        linkify=("change-update", [tables.A("uuid")]),
    )
    long_name = BackupValueColumn(
        verbose_name="Long Name",
        accessor="update__long_name",
        backup_accessor="content_object.long_name",
    )
    instrument_category = BackupValueColumn(
        verbose_name="Instrument Category",
        accessor="update__instrument_category",
        backup_accessor="content_object.instrument_category",
    )
    instrument_class = BackupValueColumn(
        verbose_name="Instrument Class",
        accessor="update__instrument_class",
        backup_accessor="content_object.instrument_class",
    )
    instrument_type = BackupValueColumn(
        verbose_name="Instrument Type",
        accessor="update__instrument_type",
        backup_accessor="content_object.instrument_type",
    )
    instrument_subtype = BackupValueColumn(
        verbose_name="Instrument Subtype",
        accessor="update__instrument_subtype",
        backup_accessor="content_object.instrument_subtype",
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
    short_name = BackupValueColumn(
        verbose_name="Short Name",
        accessor="update__short_name",
        backup_accessor="content_object.short_name",
        linkify=("change-update", [tables.A("uuid")]),
    )
    long_name = BackupValueColumn(
        verbose_name="Long Name",
        accessor="update__long_name",
        backup_accessor="content_object.long_name",
    )
    category = BackupValueColumn(
        verbose_name="Category",
        accessor="update__category",
        backup_accessor="content_object.category",
    )

    class Meta(DraftTableBase.Meta):
        all_fields = ("short_name", "long_name", "category") + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields


class GcmdPhenomenonChangeListTable(DraftTableBase):
    variable_3 = BackupValueColumn(
        verbose_name="Variable 3",
        accessor="update__variable_3",
        backup_accessor="content_object.variable_3",
        linkify=("change-update", [tables.A("uuid")]),
    )
    variable_2 = BackupValueColumn(
        verbose_name="Variable 2",
        accessor="update__variable_2",
        backup_accessor="content_object.variable_2",
    )
    variable_1 = BackupValueColumn(
        verbose_name="Variable 1",
        accessor="update__variable_1",
        backup_accessor="content_object.variable_1",
    )
    term = BackupValueColumn(
        verbose_name="Term", accessor="update__term", backup_accessor="content_object.term"
    )
    topic = BackupValueColumn(
        verbose_name="Topic", accessor="update__topic", backup_accessor="content_object.topic"
    )
    category = BackupValueColumn(
        verbose_name="Category",
        accessor="update__category",
        backup_accessor="content_object.category",
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


class AffectedRecordValueColumn(tables.Column):
    def __init__(self, resolved_accessor=None, **kwargs):
        super().__init__(**kwargs)
        self.resolved_accessor = resolved_accessor

    def render(self, **kwargs):
        total_records = kwargs.get("value")
        resolved_records = A(self.resolved_accessor).resolve(kwargs.get("record"))

        return f"{resolved_records} of {total_records} resolved"


class GcmdSyncListTable(DraftTableBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    short_name = BackupValueColumn(
        verbose_name="GCMD Keyword",
        accessor="short_name",
        backup_accessor="content_object.short_name",
        linkify=("change-gcmd", [tables.A("uuid")]),
    )
    category = BackupValueColumn(
        verbose_name="Category",
        accessor="content_type__model",
        backup_accessor="content_type__model",
    )
    draft_action = BackupValueColumn(
        verbose_name="Type of Change",
        accessor="action",
        backup_accessor="action",
    )
    status = BackupValueColumn(
        verbose_name="Status",
        accessor="status",
        backup_accessor="status",
    )
    affected_records = AffectedRecordValueColumn(
        verbose_name="Affected Records",
        accessor="affected_records",
        resolved_accessor="resolved_records",
    )

    def render_category(self, value, record):
        if value == "gcmdproject":
            return "Project"
        if value == "gcmdinstrument":
            return "Instrument"
        if value == "gcmdplatform":
            return "Platform"
        if value == "gcmdphenomenon":
            return "Earth Science"

    class Meta(DraftTableBase.Meta):
        all_fields = (
            "short_name",
            "category",
            "draft_action",
            "status",
            "affected_records",
        )
        fields = list(all_fields)
        sequence = all_fields


class ImageChangeListTable(DraftTableBase):
    title = BackupValueColumn(
        verbose_name="Title",
        accessor="update__title",
        backup_accessor="content_object.title",
        linkify=("change-update", [tables.A("uuid")]),
    )

    class Meta(DraftTableBase.Meta):
        all_fields = ("title",) + DraftTableBase.final_fields
        fields = list(all_fields)
        sequence = all_fields

    def render_short_name(self, value, record):
        return format_html(
            '<a href="{form_url}">{label}</a>',
            form_url=reverse(
                'canonical-redirect',
                kwargs={
                    "canonical_uuid": record.uuid,
                    "model": camel_to_snake(record.model_name),
                },
            ),
            label=record.update.get('short_name') or '---',
        )


# This table renders a list of historical drafts
class DraftHistoryTable(tables.Table):
    draft_action = tables.Column(accessor=tables.A('action'))
    submitted_by = tables.Column(empty_values=())
    reviewed_by = tables.Column(empty_values=())
    published_by = tables.Column(empty_values=())
    published_date = tables.Column(empty_values=())

    uuid = tables.Column(
        verbose_name="UUID",
        linkify=(
            lambda record: reverse(
                "historical-detail",
                kwargs={
                    "model": camel_to_snake(record.model_name),
                    "draft_uuid": record.uuid,
                    "canonical_uuid": record.model_instance_uuid or record.uuid,
                },
            )
        ),
    )

    class Meta:
        model = Change
        template_name = "django_tables2/bootstrap.html"
        fields = ("uuid", "submitted_by")
        orderable = False

    def render_submitted_by(self, record):
        if approval := record.approvallog_set.filter(action=ApprovalLog.Actions.PUBLISH).first():
            return approval.user.username
        else:
            return "-"

    def render_reviewed_by(self, record):
        if approval := record.approvallog_set.filter(action=ApprovalLog.Actions.REVIEW).first():
            return approval.user.username
        else:
            return "-"

    def render_published_by(self, record):
        if approval := record.approvallog_set.filter(action=ApprovalLog.Actions.PUBLISH).first():
            return approval.user.username
        else:
            return "-"

    def render_published_date(self, record):
        if approval := record.approvallog_set.filter(action=ApprovalLog.Actions.PUBLISH).first():
            return approval.date
        else:
            return "not published yet"
