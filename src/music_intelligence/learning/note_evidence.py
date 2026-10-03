"""Shared note-level research evidence.

This schema makes an important distinction:

- a detected pitch event in mixed audio is a NOTE_HYPOTHESIS;
- a score/form-aligned hypothesis is still not an exact transcription;
- pianist-specific ground truth requires instrument attribution and verification.

It is designed for Legend research and keeps audio seconds as provenance while
musical position remains canonical.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .score_alignment import MusicalScoreCoordinate


class NoteEvidenceStatus(str, Enum):
    NOTE_HYPOTHESIS = "note_hypothesis"
    SCORE_ALIGNED_HYPOTHESIS = "score_aligned_hypothesis"
    INSTRUMENT_ATTRIBUTED = "instrument_attributed"
    EXPERT_VERIFIED = "expert_verified"
    GROUND_TRUTH_TRANSCRIPTION = "ground_truth_transcription"


@dataclass(frozen=True)
class NoteLevelEvidence:
    evidence_id: str
    pitch_midi: float
    coordinate: MusicalScoreCoordinate | None = None
    onset_sec: float | None = None
    offset_sec: float | None = None
    instrument: str = ""
    voice: str = ""
    status: NoteEvidenceStatus = NoteEvidenceStatus.NOTE_HYPOTHESIS
    pitch_confidence: float = 0.0
    onset_confidence: float = 0.0
    attribution_confidence: float = 0.0
    verification_confidence: float = 0.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.evidence_id:
            raise ValueError("evidence_id is required")
        if not 0.0 <= self.pitch_midi <= 127.0:
            raise ValueError("pitch_midi must lie within MIDI range")
        if self.coordinate is not None:
            self.coordinate.validate()
        if self.onset_sec is not None and self.onset_sec < 0:
            raise ValueError("onset_sec may not be negative")
        if self.offset_sec is not None:
            if self.onset_sec is None:
                raise ValueError("offset_sec requires onset_sec")
            if self.offset_sec < self.onset_sec:
                raise ValueError("offset_sec may not precede onset_sec")
        for name in (
            "pitch_confidence",
            "onset_confidence",
            "attribution_confidence",
            "verification_confidence",
        ):
            if not 0.0 <= getattr(self, name) <= 1.0:
                raise ValueError(f"{name} must be within 0..1")

        if self.status in {
            NoteEvidenceStatus.INSTRUMENT_ATTRIBUTED,
            NoteEvidenceStatus.EXPERT_VERIFIED,
            NoteEvidenceStatus.GROUND_TRUTH_TRANSCRIPTION,
        } and not self.instrument:
            raise ValueError("instrument-attributed status requires instrument")

        if self.status in {
            NoteEvidenceStatus.SCORE_ALIGNED_HYPOTHESIS,
            NoteEvidenceStatus.INSTRUMENT_ATTRIBUTED,
            NoteEvidenceStatus.EXPERT_VERIFIED,
            NoteEvidenceStatus.GROUND_TRUTH_TRANSCRIPTION,
        } and self.coordinate is None:
            raise ValueError("aligned/verified status requires musical coordinate")

        if (
            self.status is NoteEvidenceStatus.GROUND_TRUTH_TRANSCRIPTION
            and self.verification_confidence < 0.95
        ):
            raise ValueError(
                "ground-truth transcription requires verification_confidence >= .95"
            )

    @property
    def is_exact_transcription(self) -> bool:
        return self.status is NoteEvidenceStatus.GROUND_TRUTH_TRANSCRIPTION


def may_promote_as_legend_note(evidence: NoteLevelEvidence) -> bool:
    evidence.validate()
    return (
        evidence.instrument != ""
        and evidence.status in {
            NoteEvidenceStatus.EXPERT_VERIFIED,
            NoteEvidenceStatus.GROUND_TRUTH_TRANSCRIPTION,
        }
        and evidence.attribution_confidence >= 0.9
        and evidence.verification_confidence >= 0.9
    )
