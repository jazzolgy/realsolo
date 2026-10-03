from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Mapping, Sequence

from music_intelligence.reasoning.groove_context import (
    GrooveCoordinationMode,
    GrooveTemporalContext,
    groove_timing_offset_beats,
    player_phase_offset_beats,
    player_swing_offbeat_fraction,
)

ExpressionValue = float | int | str | bool


@dataclass(frozen=True, slots=True)
class RenderVoice:
    """Renderer-facing voice. Musical policy lives in Core/player workstreams."""

    pitch_midi: int
    velocity: int = 72
    duration_beats: float = 0.5
    onset_offset_beats: float = 0.0
    articulation: tuple[str, ...] = ()
    instrument_role: str = "solo"
    breath_before_beats: float = 0.0
    attack_scale: float = 1.0
    release_shape: str = "normal"
    expression_controls: Mapping[str, ExpressionValue] = field(default_factory=dict)

    def validate(self) -> None:
        if not 0 <= self.pitch_midi <= 127:
            raise ValueError("pitch_midi must be in MIDI range 0..127")
        if not 1 <= self.velocity <= 127:
            raise ValueError("velocity must be in MIDI range 1..127")
        if self.duration_beats <= 0:
            raise ValueError("duration_beats must be positive")
        if self.breath_before_beats < 0:
            raise ValueError("breath_before_beats cannot be negative")
        if self.attack_scale <= 0:
            raise ValueError("attack_scale must be positive")
        for key, value in self.expression_controls.items():
            if not key or not isinstance(key, str):
                raise ValueError("expression control keys must be non-empty strings")
            if not isinstance(value, (bool, int, float, str)):
                raise ValueError("expression control values must be JSON scalar values")


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
                "breath_before_beats": v.breath_before_beats,
                "attack_scale": v.attack_scale,
                "release_shape": v.release_shape,
                "expression_controls": dict(v.expression_controls),
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
    breath_before_beats: float = 0.0,
    attack_scale: float = 1.0,
    release_shape: str = "normal",
    expression_controls: Mapping[str, ExpressionValue] | None = None,
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
                breath_before_beats=breath_before_beats,
                attack_scale=attack_scale,
                release_shape=release_shape,
                expression_controls=dict(expression_controls or {}),
            ),
        ),
        source=source,
    )


def apply_shared_groove_to_render_gesture(
    gesture: RenderGesture,
    *,
    anchor_beat: float,
    groove: GrooveTemporalContext | None,
    phrase_maturity: float = 0.5,
) -> RenderGesture:
    """Realize a shared groove as a reference, not a universal exact onset.

    LOCKED: all players use the shared reference exactly.
    ELASTIC/HUMAN_DRIFT: each role receives bounded phrase-shaped phase and
    swing placement around the same reference pulse.
    """
    gesture.validate()
    if groove is None:
        return gesture
    groove.validate()

    def warped(v: RenderVoice) -> RenderVoice:
        role=v.instrument_role or gesture.role
        local=anchor_beat+v.onset_offset_beats
        frac=local % 1.0
        shift=0.0

        if groove.eligible_for_swing_warp():
            shared=groove.swing_offbeat_fraction
            desired=player_swing_offbeat_fraction(role,groove)
            # A nominal eighth in a main-beat gesture gets warped from .5.
            if abs(frac-.5) <= .08:
                shift += desired-frac
            # A dedicated shared swing-subbeat request starts at the shared
            # offbeat; elastic players may sit slightly around that reference.
            elif abs(frac-shared) <= .08:
                shift += desired-frac
        else:
            shift += groove_timing_offset_beats(local,groove,swing_eligible=True)

        shift += player_phase_offset_beats(
            role,
            groove,
            phrase_maturity=phrase_maturity,
        )
        return replace(v,onset_offset_beats=v.onset_offset_beats+shift)

    annotations=dict(gesture.annotations)
    annotations["groove_feel"]=groove.feel.value
    annotations["groove_grammar"]=groove.grammar_id
    annotations["swing_ratio"]=f"{groove.effective_swing_ratio:.4f}"
    annotations["groove_coordination_mode"]=groove.coordination_mode.value
    tags=tuple(dict.fromkeys((
        *gesture.tags,
        f"groove:{groove.feel.value}",
        f"groove_mode:{groove.coordination_mode.value}",
    )))
    out=replace(
        gesture,
        voices=tuple(warped(v) for v in gesture.voices),
        drum_hits=tuple(warped(v) for v in gesture.drum_hits),
        tags=tags,
        annotations=annotations,
    )
    out.validate()
    return out

