"""Audio -> shared structure -> all-domain learning artifacts."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol

from music_intelligence.corpus.registry import CorpusItem, CorpusUse
from .representation import LearningArtifact, StructuralPerformanceData
from .extractors import DEFAULT_EXTRACTORS, LearningExtractor, extract_learning_artifacts
from .style import build_style_artifact
from .genre import build_genre_artifact
from .groove import build_groove_artifact


class AudioAnalysisAdapter(Protocol):
    """Pluggable audio front-end: separation/transcription/analysis may evolve."""

    def analyze(
        self,
        audio_path: Path,
        *,
        source_item: CorpusItem,
    ) -> StructuralPerformanceData:
        ...


class LearningDisposition(str,Enum):
    TRAINING_ELIGIBLE="training_eligible"
    DERIVED_ONLY="derived_only"


@dataclass(frozen=True)
class LearningConversion:
    source_item_id: str
    structural_data: StructuralPerformanceData
    artifacts: tuple[LearningArtifact,...]
    disposition: LearningDisposition
    rights_reason: str
    structure_eligible: bool = False
    structure_reason: str = ""

    @property
    def training_artifacts(self) -> tuple[LearningArtifact,...]:
        return (
            self.artifacts
            if (
                self.disposition is LearningDisposition.TRAINING_ELIGIBLE
                and self.structure_eligible
            )
            else ()
        )

    @property
    def derived_artifacts(self) -> tuple[LearningArtifact,...]:
        return self.artifacts


def _rights(item: CorpusItem) -> tuple[LearningDisposition,str]:
    if CorpusUse.TRAINING in item.uses and item.rights.permits(CorpusUse.TRAINING) is True:
        return LearningDisposition.TRAINING_ELIGIBLE,"explicit training permission"
    return LearningDisposition.DERIVED_ONLY,(
        "converted to shared structural/derived data; model-training admission "
        "requires explicit training permission"
    )


def convert_audio_to_learning_data(
    item: CorpusItem,
    audio_path: Path,
    analyzer: AudioAnalysisAdapter,
    *,
    extractors: tuple[LearningExtractor,...]=DEFAULT_EXTRACTORS,
) -> LearningConversion:
    item.validate()
    if not item.media_type.lower().startswith("audio"):
        raise ValueError("learning conversion requires an audio corpus item")
    structural=analyzer.analyze(audio_path,source_item=item)
    structural.validate()
    if structural.source_id != item.item_id:
        raise ValueError("structural source_id must match CorpusItem.item_id")
    structure_eligible = bool(structural.events) and all(
        event.musical_position is not None for event in structural.events
    )
    structure_reason = (
        "all performance events carry canonical musical coordinates"
        if structure_eligible
        else (
            "derived/navigation evidence only; every training event must carry "
            "a canonical musical coordinate"
        )
    )
    base_artifacts=extract_learning_artifacts(structural,extractors)
    extras=tuple(x for x in (
        build_style_artifact(structural,base_artifacts),
        build_genre_artifact(structural,base_artifacts),
        build_groove_artifact(structural),
    ) if x is not None)
    artifacts=base_artifacts+extras
    disposition,reason=_rights(item)
    return LearningConversion(
        source_item_id=item.item_id,
        structural_data=structural,
        artifacts=artifacts,
        disposition=disposition,
        rights_reason=reason,
        structure_eligible=structure_eligible,
        structure_reason=structure_reason,
    )
