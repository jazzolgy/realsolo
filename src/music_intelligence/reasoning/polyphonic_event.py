"""Shared additive polyphonic event representation.

CR-001: instrument-neutral sonority / orchestration semantics.
This module does not replace monophonic CandidateEvent.

Important: one polyphonic action does not imply sample-accurate simultaneity.
Each voice may carry its own onset offset, so a single committed sonority may
be slightly rolled, arpeggiated, spread, or otherwise near-simultaneous.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Mapping


@dataclass(frozen=True)
class InstrumentAssignment:
    instrument_id: str | None = None
    instrument_family: str | None = None
    section_id: str | None = None
    part_id: str | None = None


@dataclass(frozen=True)
class VoiceEvent:
    voice_id: str
    pitch_midi: int
    # Relative to the PolyphonicEventCandidate anchor. Values need not be equal.
    # Positive and negative values are allowed so expressive spread can straddle
    # the nominal group onset when the scheduler supports it.
    onset_offset_beats: float = 0.0
    duration_beats: float | None = None
    velocity: int | None = None
    articulation: tuple[str, ...] = ()
    harmonic_role: str | None = None
    assignment: InstrumentAssignment | None = None
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.voice_id:
            raise ValueError("voice_id is required")
        if not 0 <= self.pitch_midi <= 127:
            raise ValueError("pitch_midi must be in MIDI range 0..127")
        if self.duration_beats is not None and self.duration_beats <= 0:
            raise ValueError("voice duration must be positive")
        if self.velocity is not None and not 1 <= self.velocity <= 127:
            raise ValueError("voice velocity must be in MIDI range 1..127")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


@dataclass(frozen=True)
class DoublingRelation:
    voice_ids: tuple[str, ...]
    relation: str = "unison_or_octave"

    def validate(self, known_voice_ids: set[str]) -> None:
        if len(self.voice_ids) < 2:
            raise ValueError("doubling requires at least two voices")
        if any(v not in known_voice_ids for v in self.voice_ids):
            raise ValueError("doubling references unknown voice_id")


@dataclass(frozen=True)
class VoiceLeadingRelation:
    from_voice_id: str
    to_voice_id: str
    semitone_motion: int | None = None
    relation: str = "continuation"


@dataclass(frozen=True)
class TopNoteConstraint:
    target_pitch_midi: int | None = None
    target_pitch_class: int | None = None
    voice_id: str | None = None
    required: bool = True

    def validate(self) -> None:
        if self.target_pitch_midi is not None and not 0 <= self.target_pitch_midi <= 127:
            raise ValueError("top-note MIDI pitch must be within 0..127")
        if self.target_pitch_class is not None and not 0 <= self.target_pitch_class <= 11:
            raise ValueError("top-note pitch class must be within 0..11")


@dataclass(frozen=True)
class BassRelation:
    bass_voice_id: str
    harmonic_role: str | None = None
    interval_from_root: int | None = None


@dataclass(frozen=True)
class PolyphonicEventCandidate:
    """One immediately playable polyphonic gesture containing one or more voices.

    "One action" means one current musical decision/gesture. It does NOT mean
    every note has the same physical onset. VoiceEvent.onset_offset_beats may
    distribute the notes around the gesture anchor.
    """
    voices: tuple[VoiceEvent, ...]
    duration_beats: float
    onset_offset_beats: float = 0.0
    velocity: int = 72
    articulation: tuple[str, ...] = ()
    tags: frozenset[str] = frozenset()
    role: str = "sonority"
    source_family: str = "polyphonic_generated"
    top_note_constraint: TopNoteConstraint | None = None
    bass_relation: BassRelation | None = None
    doublings: tuple[DoublingRelation, ...] = ()
    voice_leading: tuple[VoiceLeadingRelation, ...] = ()
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()
    annotations: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.voices:
            raise ValueError("polyphonic candidate must contain at least one voice")
        if self.duration_beats <= 0:
            raise ValueError("duration_beats must be positive")
        if not 1 <= self.velocity <= 127:
            raise ValueError("velocity must be in MIDI range 1..127")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        ids = [v.voice_id for v in self.voices]
        if len(ids) != len(set(ids)):
            raise ValueError("voice_id values must be unique within a sonority")
        known = set(ids)
        for voice in self.voices:
            voice.validate()
        for rel in self.doublings:
            rel.validate(known)
        for rel in self.voice_leading:
            if rel.to_voice_id not in known:
                raise ValueError("voice-leading target references unknown current voice_id")
        if self.top_note_constraint is not None:
            self.top_note_constraint.validate()
            if self.top_note_constraint.voice_id is not None and self.top_note_constraint.voice_id not in known:
                raise ValueError("top-note constraint references unknown voice_id")
        if self.bass_relation is not None and self.bass_relation.bass_voice_id not in known:
            raise ValueError("bass relation references unknown voice_id")

    @property
    def ordered_voices(self) -> tuple[VoiceEvent, ...]:
        return self.voices

    @property
    def pitches_midi(self) -> tuple[int, ...]:
        return tuple(v.pitch_midi for v in self.voices)

    @property
    def register_span_semitones(self) -> int:
        pitches = self.pitches_midi
        return max(pitches) - min(pitches)

    @property
    def spacing_semitones(self) -> tuple[int, ...]:
        pitches = sorted(self.pitches_midi)
        return tuple(b - a for a, b in zip(pitches, pitches[1:]))

    @property
    def voice_onset_spread_beats(self) -> float:
        """Physical onset spread inside this single musical gesture."""
        offsets = [v.onset_offset_beats for v in self.voices]
        return max(offsets) - min(offsets)

    @property
    def voices_by_onset(self) -> tuple[VoiceEvent, ...]:
        """Scheduling order; semantic voice order remains available separately."""
        return tuple(sorted(self.voices, key=lambda v: v.onset_offset_beats))

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["tags"] = sorted(self.tags)
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PolyphonicEventCandidate":
        voices = tuple(
            VoiceEvent(
                **{
                    **v,
                    "articulation": tuple(v.get("articulation", ())),
                    "provenance": tuple(v.get("provenance", ())),
                    "assignment": InstrumentAssignment(**v["assignment"]) if v.get("assignment") else None,
                }
            )
            for v in payload["voices"]
        )
        top = TopNoteConstraint(**payload["top_note_constraint"]) if payload.get("top_note_constraint") else None
        bass = BassRelation(**payload["bass_relation"]) if payload.get("bass_relation") else None
        doublings = tuple(
            DoublingRelation(
                voice_ids=tuple(d["voice_ids"]),
                relation=d.get("relation", "unison_or_octave"),
            )
            for d in payload.get("doublings", ())
        )
        leading = tuple(VoiceLeadingRelation(**d) for d in payload.get("voice_leading", ()))
        obj = cls(
            voices=voices,
            duration_beats=float(payload["duration_beats"]),
            onset_offset_beats=float(payload.get("onset_offset_beats", 0.0)),
            velocity=int(payload.get("velocity", 72)),
            articulation=tuple(payload.get("articulation", ())),
            tags=frozenset(payload.get("tags", ())),
            role=str(payload.get("role", "sonority")),
            source_family=str(payload.get("source_family", "polyphonic_generated")),
            top_note_constraint=top,
            bass_relation=bass,
            doublings=doublings,
            voice_leading=leading,
            confidence=float(payload.get("confidence", 1.0)),
            provenance=tuple(payload.get("provenance", ())),
            annotations=dict(payload.get("annotations", {})),
        )
        obj.validate()
        return obj
