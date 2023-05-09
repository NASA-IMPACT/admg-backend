from api_app.models import Change
from data_models.models import DOI

unpublished_dois = Change.objects.of_type(DOI).filter(status=0).exclude(status=Change.Statuses.PUBLISHED)
for doi in unpublished_dois:
    doi.delete()