from data_models.models import Campaign, DOI, CollectionPeriod
from django.db.models import ForeignKey, ManyToManyField
from django.contrib.contenttypes.fields import GenericRelation


def get_related_fields(obj):
    related_fields = [
        f
        for f in obj._meta.get_fields()
        if isinstance(f, (ForeignKey, ManyToManyField, GenericRelation))
    ]
    return related_fields


def get_related_objs(obj):
    related_fields = get_related_fields(obj)
    related_obj_list = []

    for related_field in related_fields:
        related_name = related_field.name
        if isinstance(related_field, (ManyToManyField, GenericRelation)):
            related_objects = getattr(obj, related_name).all()
            related_obj_list.extend(list(related_objects))
        elif isinstance(related_field, ForeignKey):
            related_obj = getattr(obj, related_name)
            if related_obj is not None:  # Exclude unset (None) foreign keys
                related_obj_list.append(related_obj)
    return related_obj_list


def get_all_related_objs(obj):
    related_obj_list = get_related_objs(obj)
    master_list = []
    for related_obj in related_obj_list:
        if related_obj:
            master_list.append(related_obj)
            master_list.extend(get_all_related_objs(related_obj))
    return master_list


campaign_short_name = "ACES"
campaign = Campaign.objects.get(short_name='ACES')

collection_periods = CollectionPeriod.objects.filter(deployment__campaign=campaign)
dois = DOI.objects.filter(campaigns=campaign)

all = []

for cp in collection_periods:
    all.extend(get_all_related_objs(cp))

for doi in dois:
    all.extend(get_all_related_objs(doi))
