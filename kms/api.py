import logging
from typing import Any, Dict, List
import requests
import csv

logger = logging.getLogger(__name__)

base_url = "https://gcmdservices.gsfc.nasa.gov/kms"


def kms_lookup(endpoint: str, page_num=1) -> Dict[str, Any]:
    url = f"{base_url}/{endpoint if not endpoint.startswith('/') else endpoint[1:]}"
    logger.debug(f"Fetching {url}, page {page_num}")
    r = requests.get(url, params={"format": "json", "page_num": page_num})
    try:
        r.raise_for_status()
    except requests.HTTPError:
        logger.error(f'Response from KMS: "{r.text}"')
        raise
    return r.json()


# https://gcmdservices.gsfc.nasa.gov/kms/
endpoints = {
    "get_status": "/status",
    "get_concept_fullpaths": "/concept_fullpaths/concept_uuid/${conceptId}",
    "get_concept": "/concept/${conceptId}",
    "get_concept_schemes": "/concept_schemes",
    "get_concepts_by_scheme": "/concepts/concept_scheme/${conceptScheme}",
    "get_concepts_by_scheme_pattern": "/concepts/concept_scheme/${conceptScheme}/pattern/${pattern}",
    "get_concepts_all": "/concepts",
    "get_concepts_root": "/concepts/root",
    "get_concepts_by_pattern": "/concepts/pattern/${pattern}",
    "get_concept_by_short_name": "/concept/short_name/${short_name}",
    "get_concept_by_alt_label": "/concept/alt_label/${alt_label}",
    "get_concept_versions": "/concept_versions/version_type/${versionType}",
}


def fetch_keyword_list(scheme: str) -> List[Dict[str, any]]:
    url = f"https://gcmd.earthdata.nasa.gov/kms/concepts/concept_scheme/{scheme}"
    r = requests.get(url, params={"format": "csv"})
    csv_contents = r.content.decode('utf-8')
    # Skip first line of CSV, it is junk
    csv_contents = csv_contents.splitlines()[1:]
    return list(csv.DictReader(csv_contents))
