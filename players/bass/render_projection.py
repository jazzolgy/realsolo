"""Bass renderer projection.

Projects one already-chosen BassActionCandidate into renderer-facing fields.
No musical selection happens here. This is the final one-way bridge from the
bass player's committed musical/performance decision into scheduling/rendering.
"""
from __future__ import annotations

from dataclasses import dataclass

from .immediate_realizer import BassActionCandidate


@dataclass(frozen=True)
class BassRenderEvent:
    pitch_midi: int
    velocity: int
    duration_beats: float
    onset_offset_beats: float
    articulation: tuple[str, ...]
    instrument_role: str = "bass"
    ghost_opportunity: float = 0.0

    def validate(self) -> None:
        if not 0 <= self.pitch_midi <= 127:
            raise ValueError("pitch_midi must be in MIDI range")
        if not 1 <= self.velocity <= 127:
            raise ValueError("velocity must be in MIDI range 1..127")
        if self.duration_beats <= 0:
            raise ValueError("duration_beats must be positive")
        if not -0.25 <= self.onset_offset_beats <= 0.25:
            raise ValueError("onset offset must remain local to the current beat")
        if not 0.0 <= self.ghost_opportunity <= 1.0:
            raise ValueError("ghost_opportunity must be within 0..1")


def _accent_to_velocity(accent: float) -> int:
    # Keep enough headroom for later instrument/legend dynamics.
    return int(round(42 + max(0.0, min(1.0, accent)) * 68))


def project_bass_candidate_to_render_event(
    candidate: BassActionCandidate,
    *,
    tempo_bpm: float,
) -> BassRenderEvent:
    """Project a committed bass candidate into renderer data.

    microtiming_ms is converted relative to the authoritative beat duration.
    Sounding length modifies note-off timing while leaving notated duration in
    the musical event untouched.
    """
    if tempo_bpm <= 0:
        raise ValueError("tempo_bpm must be positive")
    if candidate.event.pitch_midi is None:
        raise ValueError("bass render event requires a pitched committed event")

    expr = candidate.expression
    beat_ms = 60000.0 / tempo_bpm
    onset_offset_beats = (
        candidate.event.onset_offset_beats
        + expr.microtiming_ms / beat_ms
    )
    duration_beats = candidate.event.duration_beats * expr.sounding_length_ratio

    articulation = tuple(dict.fromkeys((
        candidate.grammar.articulation_intent.value,
        expr.articulation.value,
    )))

    rendered = BassRenderEvent(
        pitch_midi=candidate.event.pitch_midi,
        velocity=_accent_to_velocity(expr.accent),
        duration_beats=max(.05, duration_beats),
        onset_offset_beats=max(-.25, min(.25, onset_offset_beats)),
        articulation=articulation,
        ghost_opportunity=expr.ghost_opportunity,
    )
    rendered.validate()
    return rendered
