"""Bridge uncertainty-preserving audio evidence into Shared Learning structure."""
from __future__ import annotations

from typing import Iterable, Mapping

from music_intelligence.learning.representation import (
    StructuralPerformanceData,
    StructuralPerformanceEvent,
)

from .schemas.evidence import AudioEventHypothesis


def _top(probabilities: Mapping[str, float]) -> tuple[str, float, float]:
    items = sorted(probabilities.items(), key=lambda kv: kv[1], reverse=True)
    if not items:
        return "", 0.0, 0.0
    return (
        items[0][0],
        float(items[0][1]),
        float(items[1][1]) if len(items) > 1 else 0.0,
    )


def to_structural_performance_data(
    source_id: str,
    events: Iterable[AudioEventHypothesis],
    *,
    tempo_bpm: float | None = None,
    meter: str = "",
    key_center: str = "",
    form_label: str = "",
    minimum_instrument_probability: float = 0.70,
    minimum_instrument_margin: float = 0.15,
) -> StructuralPerformanceData:
    """Project evidence into the existing shared-learning contract.

    Ambiguous ownership is preserved in instrument_probabilities and the legacy
    scalar instrument field is left blank unless the posterior is strong enough.
    """
    out: list[StructuralPerformanceEvent] = []
    for raw in events:
        event = raw.normalized()
        if event.source_id != source_id:
            raise ValueError("all events must match source_id")
        if event.beat_position is None or event.duration_beats is None:
            raise ValueError(
                "beat_position and duration_beats are required for structural projection"
            )

        instrument, top_p, runner_p = _top(event.instrument_probabilities)
        if (
            top_p < minimum_instrument_probability
            or top_p - runner_p < minimum_instrument_margin
        ):
            instrument = ""
        role, _, _ = _top(event.role_probabilities)
        fields = {
            k: v
            for k, v in event.confidence.as_dict().items()
            if v is not None
        }
        legacy_conf = min(fields.values()) if fields else 1.0

        out.append(StructuralPerformanceEvent(
            event_id=event.event_id,
            onset_beats=event.beat_position,
            duration_beats=event.duration_beats,
            pitch_midi=event.pitch_midi,
            unpitched_token=event.unpitched_token,
            instrument=instrument,
            role=role,
            dynamic=event.dynamic,
            accent=event.accent,
            timing_offset_beats=event.timing_offset_beats,
            articulation=event.articulation,
            harmony_label=event.harmony_context,
            phrase_id=event.phrase_id,
            ensemble_role=role,
            confidence=legacy_conf,
            tags=frozenset({event.status.value}),
            provenance=event.provenance,
            instrument_probabilities=dict(event.instrument_probabilities),
            role_probabilities=dict(event.role_probabilities),
            confidence_fields=fields,
        ))

    data = StructuralPerformanceData(
        source_id=source_id,
        events=tuple(out),
        tempo_bpm=tempo_bpm,
        meter=meter,
        key_center=key_center,
        form_label=form_label,
        provenance=("shared_audio_intelligence",),
    )
    data.validate()
    return data
