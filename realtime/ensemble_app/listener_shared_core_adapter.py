"""Adapter from listener/detector form estimates to canonical Shared coordinates.

Detector/runtime estimates are ephemeral. Persisted learning/comparison uses
MusicalScoreCoordinate only.
"""
from __future__ import annotations

from typing import Mapping

from music_intelligence.corpus.realchord import RealChordSong, coordinate_from_realchord
from music_intelligence.learning.score_alignment import (
    MusicalScoreCoordinate,
    PerformancePhase,
)


def coordinate_from_listener_estimate(
    estimate: Mapping[str, object] | None,
    *,
    song_id: str,
    performance_phase: PerformancePhase = PerformancePhase.UNKNOWN,
    realchord_song: RealChordSong | None = None,
    confidence: float = .5,
) -> MusicalScoreCoordinate | None:
    if estimate is None:
        return None

    measure_raw=estimate.get("measure_index", estimate.get("bar"))
    beat_raw=estimate.get("beat_in_measure", estimate.get("beat"))
    chorus_raw=estimate.get("chorus_index", estimate.get("chorus"))
    section=str(estimate.get("section","") or "")
    form_len_raw=estimate.get("form_length_bars")

    measure=(int(measure_raw)+1) if isinstance(measure_raw,int) and measure_raw >= 0 else None
    beat=float(beat_raw) if isinstance(beat_raw,(int,float)) else None
    chorus=int(chorus_raw) if isinstance(chorus_raw,int) and chorus_raw >= 0 else None

    # RealChord owns Expected Harmony / form identity when available.
    if realchord_song is not None and measure is not None:
        realchord_song.validate()
        if measure <= (realchord_song.form_length_bars or 0):
            return coordinate_from_realchord(
                realchord_song,
                measure=measure,
                beat=(beat+1.0 if beat is not None and beat < 1.0 else beat),
                chorus_index=chorus,
                performance_phase=performance_phase,
                confidence=confidence,
            )

    form_length=int(form_len_raw) if isinstance(form_len_raw,int) and form_len_raw > 0 else None
    if measure is None and not section:
        return None

    coord=MusicalScoreCoordinate(
        song_id=song_id,
        score_source_id="listener_detector_estimate",
        section=section,
        bar=measure,
        beat=beat if measure is not None else None,
        form_length_bars=form_length,
        form_bar=measure if form_length is not None and measure is not None and measure <= form_length else None,
        chorus_index=chorus,
        performance_phase=performance_phase,
        arrangement_segment="core_form" if measure is not None else "",
        within_core_form=True if measure is not None else None,
        confidence=max(0.0,min(1.0,confidence)),
        provenance=("autonomous_listener_detector_estimate","canonical_coordinate_adapter"),
    )
    coord.validate()
    return coord
