from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class RenderVoice:
    """Renderer-facing voice. Musical policy lives in Core/player workstreams."""

    pitch_midi: int
    velocity: int = 72
    duration_beats: float = 0.5
    onset_offset_beats: float = 0.0
    articulation: tuple[str, ...] = ()
    instrument_role: str = "solo"

    def validate(self) -> None:
        if not 0 <= self.pitch_midi <= 127:
            raise ValueError("pitch_midi must be in MIDI range 0..127")
        if not 1 <= self.velocity <= 127:
            raise ValueError("velocity must be in MIDI range 1..127")
        if self.duration_beats <= 0:
            raise ValueError("duration_beats must be positive")


@dataclass(frozen=True, slots=True)
class RenderGesture:
    """One immediately committed gesture delivered to the app renderer."""

    role: str
    voices: tuple[RenderVoice, ...] = ()
    drum_hits: tuple[RenderVoice, ...] = ()
    source: str = "player"
    tags: tuple[str, ...] = ()
    annotations: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        for voice in self.voices + self.drum_hits:
            voice.validate()

    def to_dict(self) -> dict:
        self.validate()

        def voice_dict(v: RenderVoice) -> dict:
            return {
                "pitch_midi": v.pitch_midi,
                "velocity": v.velocity,
                "duration_beats": v.duration_beats,
                "onset_offset_beats": v.onset_offset_beats,
                "articulation": list(v.articulation),
                "instrument_role": v.instrument_role,
            }

        return {
            "role": self.role,
            "voices": [voice_dict(v) for v in self.voices],
            "drum_hits": [voice_dict(v) for v in self.drum_hits],
            "source": self.source,
            "tags": list(self.tags),
            "annotations": dict(self.annotations),
        }


def fallback_accompaniment_gesture(frame: Mapping, *, beat_duration: float = 1.0) -> RenderGesture:
    """Temporary adapter for the app-local fallback accompaniment.

    Bass/drum/piano player branches should eventually produce equivalent
    committed gestures directly. This function deliberately contains no
    musical intelligence.
    """

    voices: list[RenderVoice] = []
    for note in frame.get("bass", ()):
        voices.append(RenderVoice(note, 92, 0.82, instrument_role="bass"))
    for note in frame.get("comp", ()):
        voices.append(RenderVoice(note, 68, 0.58, 0.05, instrument_role="piano"))

    drums = frame.get("drums", {})
    hits: list[RenderVoice] = []
    if drums.get("ride"):
        hits.append(RenderVoice(51, 58, 0.12, instrument_role="drums"))
    if drums.get("hat"):
        hits.append(RenderVoice(42, 70, 0.08, 0.02, instrument_role="drums"))
    if drums.get("kick"):
        hits.append(RenderVoice(36, 76, 0.10, instrument_role="drums"))

    return RenderGesture(
        role="accompaniment",
        voices=tuple(voices),
        drum_hits=tuple(hits),
        source="realtime_fallback",
        tags=("temporary_fallback",),
    )


def monophonic_solo_gesture(
    pitch_midi: int,
    duration_beats: float,
    *,
    velocity: int = 82,
    articulation: tuple[str, ...] = (),
    instrument_role: str = "tenor_sax",
    source: str = "core_immediate",
) -> RenderGesture:
    return RenderGesture(
        role="soloist",
        voices=(
            RenderVoice(
                pitch_midi,
                velocity,
                duration_beats,
                articulation=articulation,
                instrument_role=instrument_role,
            ),
        ),
        source=source,
    )
