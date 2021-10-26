from dataclasses import dataclass
from typing import List
import uuid


@dataclass(frozen=True)
class ConceptScheme:
    shortName: str
    longName: str


@dataclass(frozen=True)
class ConceptDefinition:
    text: str
    reference: str


@dataclass(frozen=True)
class Concept:
    id: int
    uuid: uuid.UUID
    prefLabel: str
    isLeaf: bool
    scheme: ConceptScheme
    definitions: List[ConceptDefinition]
