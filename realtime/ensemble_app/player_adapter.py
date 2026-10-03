from __future__ import annotations

from typing import Mapping

from music_intelligence.reasoning.polyphonic_event import PolyphonicEventCandidate

from .player_contract import RenderGesture, RenderVoice


def _instrument_role(voice, default_role: str) -> str:
    assignment = voice.assignment
    if assignment is None:
        return default_role

    for value in (
        assignment.part_id,
        assignment.instrument_family,
        assignment.instrument_id,
    ):
        if value:
            normalized = value.lower()
            if "bass" in normalized:
                return "bass"
            if "drum" in normalized or "percussion" in normalized:
                return "drums"
            if "piano" in normalized or "keyboard" in normalized:
                return "piano"
            if any(x in normalized for x in ("sax", "trumpet", "clarinet", "voice", "solo")):
                return "solo"
    return default_role


def committed_polyphonic_to_render_gesture(
    event: PolyphonicEventCandidate,
    *,
    player_role: str,
    source: str | None = None,
    annotations: Mapping[str, str] | None = None,
) -> RenderGesture:
    """Project one already-selected Core/player event into renderer data.

    This function performs no candidate evaluation and no musical selection.
    It is intentionally a one-way projection after the player has committed.
    """

    event.validate()
    voices: list[RenderVoice] = []
    drums: list[RenderVoice] = []

    for voice in event.voices_by_onset:
        role = _instrument_role(voice, player_role)
        duration = (
            voice.duration_beats
            if voice.duration_beats is not None
            else event.duration_beats
        )
        velocity = voice.velocity if voice.velocity is not None else event.velocity
        render_voice = RenderVoice(
            pitch_midi=voice.pitch_midi,
            velocity=velocity,
            duration_beats=duration,
            onset_offset_beats=event.onset_offset_beats + voice.onset_offset_beats,
            articulation=tuple(event.articulation) + tuple(voice.articulation),
            instrument_role=role,
        )
        if role == "drums":
            drums.append(render_voice)
        else:
            voices.append(render_voice)

    merged_annotations = dict(event.annotations)
    if annotations:
        merged_annotations.update(annotations)

    return RenderGesture(
        role=player_role,
        voices=tuple(voices),
        drum_hits=tuple(drums),
        source=source or event.source_family,
        tags=tuple(sorted(event.tags)),
        annotations=merged_annotations,
    )
