"""Soft source/target-instrument affinity for shared musical vocabulary.

Every Player may access every transferable vocabulary item. Affinity is only a
ranking bias; it never grants or removes access.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.legends.interfaces import (
    VocabularyDimension,
    VocabularyMemoryItem,
    VocabularyQuery,
)


@dataclass(frozen=True)
class VocabularyAffinityScore:
    source_instrument: float = 0.0
    dimensions: float = 0.0

    @property
    def total(self) -> float:
        return self.source_instrument + self.dimensions


# Same-instrument material gets a small default preference. It must remain weak
# enough that musical/contextual fit can override it.
_SAME_INSTRUMENT_BONUS = 0.10

# Cross-instrument transfer strengths are dimension-specific. These values are
# deliberately modest priors, not stylistic laws.
_CROSS_DIMENSION_AFFINITY: dict[
    tuple[str, str, VocabularyDimension], float
] = {
    # Melodic instruments can often exchange interval/contour/target behavior.
    ("sax", "piano", VocabularyDimension.PITCH_INTERVAL): 0.040,
    ("sax", "piano", VocabularyDimension.CONTOUR): 0.045,
    ("sax", "piano", VocabularyDimension.TARGET_BEHAVIOR): 0.045,
    ("piano", "sax", VocabularyDimension.PITCH_INTERVAL): 0.040,
    ("piano", "sax", VocabularyDimension.CONTOUR): 0.045,
    ("piano", "sax", VocabularyDimension.TARGET_BEHAVIOR): 0.045,

    ("sax", "bass", VocabularyDimension.CONTOUR): 0.025,
    ("sax", "bass", VocabularyDimension.RHYTHM): 0.030,
    ("sax", "bass", VocabularyDimension.TARGET_BEHAVIOR): 0.035,
    ("bass", "sax", VocabularyDimension.CONTOUR): 0.025,
    ("bass", "sax", VocabularyDimension.RHYTHM): 0.030,
    ("bass", "sax", VocabularyDimension.TARGET_BEHAVIOR): 0.035,

    ("piano", "bass", VocabularyDimension.CONTOUR): 0.025,
    ("piano", "bass", VocabularyDimension.RHYTHM): 0.030,
    ("piano", "bass", VocabularyDimension.TARGET_BEHAVIOR): 0.035,
    ("bass", "piano", VocabularyDimension.CONTOUR): 0.025,
    ("bass", "piano", VocabularyDimension.RHYTHM): 0.030,
    ("bass", "piano", VocabularyDimension.TARGET_BEHAVIOR): 0.035,

    # Drum vocabulary transfers mainly through non-pitch dimensions.
    ("drums", "piano", VocabularyDimension.RHYTHM): 0.055,
    ("drums", "piano", VocabularyDimension.ACCENT): 0.050,
    ("drums", "piano", VocabularyDimension.PHRASE_SHAPE): 0.040,
    ("drums", "piano", VocabularyDimension.DENSITY_ARC): 0.040,
    ("drums", "sax", VocabularyDimension.RHYTHM): 0.055,
    ("drums", "sax", VocabularyDimension.ACCENT): 0.045,
    ("drums", "sax", VocabularyDimension.PHRASE_SHAPE): 0.040,
    ("drums", "sax", VocabularyDimension.DENSITY_ARC): 0.035,
    ("drums", "bass", VocabularyDimension.RHYTHM): 0.055,
    ("drums", "bass", VocabularyDimension.ACCENT): 0.045,
    ("drums", "bass", VocabularyDimension.PHRASE_SHAPE): 0.040,
    ("drums", "bass", VocabularyDimension.DENSITY_ARC): 0.035,

    # Other instruments can transfer rhythmic identity to drums without
    # pretending that pitch content maps directly to the kit.
    ("piano", "drums", VocabularyDimension.RHYTHM): 0.045,
    ("piano", "drums", VocabularyDimension.ACCENT): 0.040,
    ("piano", "drums", VocabularyDimension.PHRASE_SHAPE): 0.040,
    ("piano", "drums", VocabularyDimension.DENSITY_ARC): 0.035,
    ("sax", "drums", VocabularyDimension.RHYTHM): 0.045,
    ("sax", "drums", VocabularyDimension.ACCENT): 0.040,
    ("sax", "drums", VocabularyDimension.PHRASE_SHAPE): 0.040,
    ("sax", "drums", VocabularyDimension.DENSITY_ARC): 0.035,
    ("bass", "drums", VocabularyDimension.RHYTHM): 0.045,
    ("bass", "drums", VocabularyDimension.ACCENT): 0.040,
    ("bass", "drums", VocabularyDimension.PHRASE_SHAPE): 0.040,
    ("bass", "drums", VocabularyDimension.DENSITY_ARC): 0.035,
}

_SAME_DIMENSION_BONUS: dict[VocabularyDimension, float] = {
    VocabularyDimension.PITCH_INTERVAL: 0.030,
    VocabularyDimension.RHYTHM: 0.025,
    VocabularyDimension.CONTOUR: 0.025,
    VocabularyDimension.ACCENT: 0.020,
    VocabularyDimension.DENSITY_ARC: 0.015,
    VocabularyDimension.PHRASE_SHAPE: 0.020,
    VocabularyDimension.TENSION_RELEASE: 0.020,
    VocabularyDimension.TARGET_BEHAVIOR: 0.025,
    VocabularyDimension.INTERACTION_ROLE: 0.015,
    VocabularyDimension.ARTICULATION: 0.030,
    VocabularyDimension.REGISTER_TRAJECTORY: 0.020,
}


def _norm(instrument: str) -> str:
    return instrument.strip().lower().replace("-", "_")


def source_instrument_affinity(
    source_instrument: str,
    target_instrument: str,
) -> float:
    source = _norm(source_instrument)
    target = _norm(target_instrument)
    if not source or not target:
        return 0.0
    return _SAME_INSTRUMENT_BONUS if source == target else 0.0


def dimension_affinity(
    source_instrument: str,
    target_instrument: str,
    dimensions: frozenset[VocabularyDimension],
) -> float:
    source = _norm(source_instrument)
    target = _norm(target_instrument)
    if not source or not target or not dimensions:
        return 0.0

    if source == target:
        # Average instead of summing so items with more metadata do not win just
        # because more dimensions were annotated.
        return sum(_SAME_DIMENSION_BONUS.get(d, 0.0) for d in dimensions) / len(dimensions)

    values = [
        _CROSS_DIMENSION_AFFINITY.get((source, target, dimension), 0.0)
        for dimension in dimensions
    ]
    return sum(values) / len(values)


def vocabulary_affinity(
    item: VocabularyMemoryItem,
    request: VocabularyQuery,
) -> VocabularyAffinityScore:
    target = request.target_instrument
    if not target:
        return VocabularyAffinityScore()

    # Prefer the explicitly requested transferable dimensions when supplied;
    # otherwise score the dimensions actually carried by the item.
    dimensions = request.required_dimensions or item.dimensions
    return VocabularyAffinityScore(
        source_instrument=source_instrument_affinity(
            item.source_instrument,
            target,
        ),
        dimensions=dimension_affinity(
            item.source_instrument,
            target,
            frozenset(dimensions),
        ),
    )
