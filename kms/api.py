from typing import Any, Dict, Generator
import requests

from . import models

base_url = "https://gcmdservices.gsfc.nasa.gov/kms"


def kms_lookup(url: str) -> Dict[str, Any]:
    r = requests.get(
        url,
        params={"format": "json"},
    )
    try:
        r.raise_for_status()
    except requests.HTTPError:
        print(r.text)
        raise
    return r.json()


def list_concepts(scheme: str, pattern="*") -> Generator[models.Concept, None, None]:
    url = f"{base_url}/concepts/concept_scheme/{scheme}/pattern/{pattern}"
    for concept in kms_lookup(url)["concepts"]:
        yield models.Concept(
            scheme=models.ConceptScheme(**concept.pop("scheme")),
            definitions=[
                models.ConceptDefinition(**definition)
                for definition in concept.pop("definitions")
            ],
            **concept,
        )
