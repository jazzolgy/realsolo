"""Adapters from canonical Shared Core into one realtime decision tick.

This module owns no form theory, harmony corpus, or expressive policy. It only
consumes the canonical contracts:
- MusicalScoreCoordinate
- RealChord Expected Harmony
- Shared Expression
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.corpus.realchord import (
    ExpectedHarmonyReference,
    RealChordSong,
    coordinate_from_realchord,
    expected_harmony_at,
)
from music_intelligence.expression import (
    ExpressiveContext,
    ExpressiveIntent,
    ExpressivePhase,
    realize_expressive_intent,
)
from music_intelligence.learning.score_alignment import (
    MusicalScoreCoordinate,
    PerformancePhase,
)


@dataclass(frozen=True)
class SharedCoreRuntimeTick:
    position: MusicalScoreCoordinate
    expected_harmony: ExpectedHarmonyReference | None
    expressive_intents: dict[str, ExpressiveIntent]


def _phase_for_phrase(phrase_maturity: float) -> ExpressivePhase:
    if phrase_maturity < .15:
        return ExpressivePhase.ENTRY
    if phrase_maturity < .60:
        return ExpressivePhase.DEVELOP
    if phrase_maturity < .82:
        return ExpressivePhase.PEAK
    return ExpressivePhase.RELEASE


def build_shared_core_runtime_tick(
    *,
    song_id: str,
    section: str,
    bar_index: int,
    beat_in_bar: float,
    total_bars: int,
    chorus_index: int,
    performance_phase: PerformancePhase,
    phrase_maturity: float,
    tension: float,
    ensemble_density: float,
    realchord_song: RealChordSong | None = None,
) -> SharedCoreRuntimeTick:
    """Resolve canonical position + expected harmony + HOW intent.

    Runtime beat_in_bar is zero-based. RealChord chord beats are one-based, so
    the adapter performs that representation conversion locally.
    """
    if total_bars < 1:
        raise ValueError("total_bars must be positive")
    if bar_index < 0:
        raise ValueError("bar_index may not be negative")
    if beat_in_bar < 0:
        raise ValueError("beat_in_bar may not be negative")

    expected: ExpectedHarmonyReference | None = None
    if realchord_song is not None:
        measure=bar_index+1
        rc_beat=beat_in_bar+1.0
        position=coordinate_from_realchord(
            realchord_song,
            measure=measure,
            beat=rc_beat,
            chorus_index=chorus_index,
            performance_phase=performance_phase,
        )
        expected=expected_harmony_at(
            realchord_song,
            measure=measure,
            beat=rc_beat,
        )
    else:
        position=MusicalScoreCoordinate(
            song_id=song_id,
            score_source_id="runtime_chart",
            section=section,
            bar=bar_index+1,
            beat=beat_in_bar,
            form_length_bars=total_bars,
            form_bar=bar_index+1,
            chorus_index=chorus_index,
            performance_phase=performance_phase,
            arrangement_segment="core_form",
            within_core_form=True,
            confidence=.85,
            provenance=("realtime_chart_adapter",),
        )
        position.validate()

    phase=_phase_for_phrase(phrase_maturity)
    intents={}
    targets={
        "sax": .72,
        "piano": .30,
        "bass": .38,
        "drums": .34,
    }
    for player_id,target_foreground in targets.items():
        context=ExpressiveContext(
            position=position,
            phrase_maturity=max(0.0,min(1.0,phrase_maturity)),
            tension=max(0.0,min(1.0,tension)),
            ensemble_density=max(0.0,min(1.0,ensemble_density)),
            current_foreground_weight=target_foreground,
            target_foreground_weight=target_foreground,
            boundary_pressure=(
                .72 if position.distance_to_form_end is not None
                and position.distance_to_form_end <= 1 else .18
            ),
            climax_pressure=max(0.0,min(1.0,tension-.15)),
            release_pressure=.68 if phase is ExpressivePhase.RELEASE else .12,
            expressive_phase=phase,
        )
        intents[player_id]=realize_expressive_intent(context)

    return SharedCoreRuntimeTick(
        position=position,
        expected_harmony=expected,
        expressive_intents=intents,
    )
