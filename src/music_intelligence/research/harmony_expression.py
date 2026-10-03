"""Research bridge: Expected Harmony x expressive realization.

This module joins a form-position expressive observation to RealChord Expected
Harmony without collapsing Expected / Observed / Inferred harmony.

It is intentionally instrument-neutral and does not promote mixed-audio proxy
features into player-specific performance constants.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from music_intelligence.corpus.realchord import (
    ExpectedHarmonyReference,
    RealChordSong,
    coordinate_from_realchord,
    expected_harmony_at,
)
from music_intelligence.learning.score_alignment import (
    MusicalScoreCoordinate,
    PerformancePhase,
)


@dataclass(frozen=True)
class HarmonyConditionedExpressionObservation:
    observation_id: str
    coordinate: MusicalScoreCoordinate
    expected_harmony: ExpectedHarmonyReference | None
    dynamic_proxy: float | None = None
    accent_proxy: float | None = None
    body_proxy: float | None = None
    brightness_proxy: float | None = None
    motif_id: str = ""
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.observation_id:
            raise ValueError("observation_id is required")
        self.coordinate.validate()
        if self.expected_harmony is not None:
            self.expected_harmony.validate()
            if self.expected_harmony.realchord_id != self.coordinate.realchord_id:
                raise ValueError("harmony reference and coordinate disagree")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


def build_harmony_conditioned_expression(
    *,
    observation_id: str,
    song: RealChordSong,
    measure: int,
    beat: float,
    chorus_index: int | None,
    performance_phase: PerformancePhase,
    dynamic_proxy: float | None = None,
    accent_proxy: float | None = None,
    body_proxy: float | None = None,
    brightness_proxy: float | None = None,
    motif_id: str = "",
    confidence: float = 1.0,
    provenance: tuple[str, ...] = (),
) -> HarmonyConditionedExpressionObservation:
    coordinate = coordinate_from_realchord(
        song,
        measure=measure,
        beat=beat,
        chorus_index=chorus_index,
        performance_phase=performance_phase,
        confidence=confidence,
    )
    expected = expected_harmony_at(song, measure=measure, beat=beat)
    obs = HarmonyConditionedExpressionObservation(
        observation_id=observation_id,
        coordinate=coordinate,
        expected_harmony=expected,
        dynamic_proxy=dynamic_proxy,
        accent_proxy=accent_proxy,
        body_proxy=body_proxy,
        brightness_proxy=brightness_proxy,
        motif_id=motif_id,
        confidence=confidence,
        provenance=provenance + (f"realchord:{song.realchord_id}",),
    )
    obs.validate()
    return obs


def same_expected_harmony_context(
    left: HarmonyConditionedExpressionObservation,
    right: HarmonyConditionedExpressionObservation,
    *,
    require_same_form_bar: bool = False,
) -> bool:
    """Compare HOW under the same chart harmony while preserving phase differences."""
    left.validate()
    right.validate()
    if left.expected_harmony is None or right.expected_harmony is None:
        return False
    if left.expected_harmony.chord_symbol != right.expected_harmony.chord_symbol:
        return False
    if left.coordinate.realchord_id != right.coordinate.realchord_id:
        return False
    if require_same_form_bar and left.coordinate.form_bar != right.coordinate.form_bar:
        return False
    return True


def group_by_expected_harmony(
    observations: Iterable[HarmonyConditionedExpressionObservation],
) -> dict[str, tuple[HarmonyConditionedExpressionObservation, ...]]:
    groups: dict[str, list[HarmonyConditionedExpressionObservation]] = {}
    for obs in observations:
        obs.validate()
        if obs.expected_harmony is None:
            continue
        groups.setdefault(obs.expected_harmony.chord_symbol, []).append(obs)
    return {key: tuple(value) for key, value in groups.items()}
