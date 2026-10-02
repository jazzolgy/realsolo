"""Bill Evans vocabulary memory interface.

Bill Evans owns source/provenance. Shared Vocabulary owns reusable retrieval and
cross-instrument ranking.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from music_intelligence.legends.interfaces import (
    LegendDomain,
    SignatureStatus,
    VocabularyDimension,
    VocabularyMemoryItem,
    VocabularyQuery,
    VocabularyUseType,
)
from music_intelligence.vocabulary import rank_vocabulary_items


def _enum_set(values, enum_type):
    return frozenset(enum_type(value) for value in values)


def load_bill_evans_vocabulary() -> tuple[VocabularyMemoryItem, ...]:
    data_dir=Path(__file__).with_name("data")
    items=[]
    for path in sorted(data_dir.glob("*.json")):
        payload=json.loads(path.read_text(encoding="utf-8"))
        source_id=payload.get("source_id","")
        recording_id=payload.get("recording_id","")
        for raw in payload.get("items",()):
            item=VocabularyMemoryItem(
                vocabulary_id=raw["vocabulary_id"],
                source_id=source_id,
                recording_id=recording_id,
                tune_id=raw.get("tune_id",""),
                chorus=raw.get("chorus",""),
                bar=raw.get("bar",""),
                timestamp=raw.get("timestamp",""),
                harmony_context=raw.get("harmony_context",""),
                harmonic_function=raw.get("harmonic_function",""),
                phrase_position=raw.get("phrase_position",""),
                entrance=raw.get("entrance",""),
                ending=raw.get("ending",""),
                rhythm=raw.get("rhythm",""),
                contour=raw.get("contour",""),
                interval_pattern=raw.get("interval_pattern",""),
                articulation=raw.get("articulation",""),
                register=raw.get("register",""),
                tension_curve=raw.get("tension_curve",""),
                source_instrument=raw.get("source_instrument","piano"),
                dimensions=_enum_set(raw.get("dimensions",()),VocabularyDimension),
                transferable_to=frozenset(raw.get("transferable_to",())),
                domains=_enum_set(raw.get("domains",()),LegendDomain),
                context_tags=frozenset(raw.get("context_tags",())),
                candidate_uses=_enum_set(raw.get("candidate_uses",()),VocabularyUseType),
                signature_status=SignatureStatus(raw.get("signature_status","none")),
                signature_evidence_count=int(raw.get("signature_evidence_count",0)),
                confidence=float(raw.get("confidence",1.0)),
                provenance=tuple(raw.get("provenance",())),
            )
            item.validate()
            items.append(item)
    return tuple(items)


@dataclass(frozen=True)
class BillEvansVocabularyIndex:
    items: tuple[VocabularyMemoryItem, ...] = ()

    def query(self, request: VocabularyQuery) -> tuple[VocabularyMemoryItem, ...]:
        if request.legend_id != "bill_evans":
            return ()
        return rank_vocabulary_items(self.items, request)


BILL_EVANS_VOCABULARY_INDEX = BillEvansVocabularyIndex(
    load_bill_evans_vocabulary()
)
