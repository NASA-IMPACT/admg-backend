from api_app.models import Change
from data_models.models import DOI, Campaign

created_dois_drafts = Change.objects.of_type(DOI).filter(status=0)
published_campaign_uuids = [str(uuid) for uuid in Campaign.objects.values_list("uuid",flat=True)]
dois_to_delete = []
for doi in created_dois_drafts:
    if any(uuid in doi.update.get('campaigns', []) for uuid in published_campaign_uuids):
    dois_to_delete.append(doi)

for doi in dois_to_delete:
    doi.delete()

