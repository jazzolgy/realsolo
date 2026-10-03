"""Bridge listener/runtime metric-form estimates into canonical score coordinates.

MetricFormPosition is a causal/runtime estimate. MusicalScoreCoordinate is the
persisted Shared Core coordinate used for learning, cross-source comparison,
RealChord alignment, and later retrieval.
"""
from __future__ import annotations

from music_intelligence.learning.form_position import MetricFormPosition
from music_intelligence.learning.score_alignment import (
    MusicalScoreCoordinate,
    PerformancePhase,
)


def musical_score_coordinate_from_metric_form(
    position: MetricFormPosition,
    *,
    song_id: str,
    score_source_id: str = "",
    realchord_id: str = "",
    performance_phase: PerformancePhase = PerformancePhase.UNKNOWN,
    chord_label: str = "",
    harmonic_function: str = "",
    phrase_position: str = "",
    form_role: str = "",
    navigation_state: str = "",
    arrangement_segment: str = "",
    arrangement_segment_index: int | None = None,
    within_core_form: bool | None = None,
    provenance: tuple[str,...] = (),
) -> MusicalScoreCoordinate:
    position.validate()
    if not song_id:
        raise ValueError("song_id is required")
    if realchord_id and not score_source_id:
        score_source_id=f"realchord:{realchord_id}"

    form_length=None
    form_bar=None
    if position.form_id and position.measure_index is not None:
        # MetricFormPosition does not itself carry form length. Keep exact bar
        # identity when known; callers with a FormMap/RealChord adapter should
        # replace these fields with verified form-relative values.
        form_bar=position.measure_index+1

    out=MusicalScoreCoordinate(
        song_id=song_id,
        score_source_id=score_source_id,
        realchord_id=realchord_id,
        section=position.section_id or "",
        bar=(None if position.measure_index is None else position.measure_index+1),
        beat=position.beat_in_measure,
        form_length_bars=form_length,
        form_bar=None if form_length is None else form_bar,
        chorus_index=position.form_iteration,
        performance_phase=performance_phase,
        chord_label=chord_label,
        harmonic_function=harmonic_function,
        phrase_position=phrase_position or (position.phrase_id or ""),
        form_role=form_role or (position.form_id or ""),
        navigation_state=navigation_state,
        arrangement_segment=arrangement_segment,
        arrangement_segment_index=arrangement_segment_index,
        within_core_form=within_core_form,
        confidence=position.confidence,
        provenance=position.provenance+provenance+(
            "metric_form_to_musical_score_coordinate",
        ),
    )
    out.validate()
    return out
