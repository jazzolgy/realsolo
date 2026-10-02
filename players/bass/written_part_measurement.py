"""Build measured Bass written-part evidence from structured note events.

The input may come from Transcriber/manual verification. Literal note sequences
are consumed transiently; callers may persist only the resulting abstract
profile and provenance.
"""
from __future__ import annotations

from dataclasses import dataclass

from .written_part_comparator import (
    BassLineAbstractProfile,
    BassLineObservation,
    analyze_bass_line,
)
from .written_part_evidence import (
    MeasuredWrittenPartEvidence,
    WrittenPartMeasurementStatus,
)


@dataclass(frozen=True)
class StructuredBassNote:
    pitch_midi: int
    onset_beat: float
    duration_beats: float
    harmonic_root_pc: int | None = None
    structural_pitch_classes: frozenset[int] = frozenset()
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not 0 <= self.pitch_midi <= 127:
            raise ValueError("pitch_midi must be in MIDI range")
        if self.onset_beat < 0:
            raise ValueError("onset_beat cannot be negative")
        if self.duration_beats <= 0:
            raise ValueError("duration_beats must be positive")
        if self.harmonic_root_pc is not None and not 0 <= self.harmonic_root_pc <= 11:
            raise ValueError("harmonic_root_pc must be in 0..11")
        if any(not 0 <= pc <= 11 for pc in self.structural_pitch_classes):
            raise ValueError("structural pitch classes must be in 0..11")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


def measure_written_bass_part(
    *,
    study_id: str,
    song_id: str,
    source_book_id: str,
    source_page: int,
    notes: tuple[StructuredBassNote, ...],
    verified: bool = False,
) -> MeasuredWrittenPartEvidence:
    if not notes:
        raise ValueError("written bass measurement requires note events")
    for note in notes:
        note.validate()

    ordered = tuple(sorted(notes, key=lambda x: (x.onset_beat, x.pitch_midi)))
    observations = tuple(
        BassLineObservation(
            pitch_midi=n.pitch_midi,
            beat=n.onset_beat,
            harmonic_root_pc=n.harmonic_root_pc,
            structural_pitch_classes=n.structural_pitch_classes,
            duration_beats=n.duration_beats,
        )
        for n in ordered
    )
    profile: BassLineAbstractProfile = analyze_bass_line(observations)

    confidence = min(n.confidence for n in ordered)
    provenance = tuple(dict.fromkeys(
        p for n in ordered for p in n.provenance
    ))
    return MeasuredWrittenPartEvidence(
        study_id=study_id,
        song_id=song_id,
        source_book_id=source_book_id,
        source_page=source_page,
        status=(
            WrittenPartMeasurementStatus.VERIFIED_PROFILE
            if verified
            else WrittenPartMeasurementStatus.MEASURED_PROFILE
        ),
        confidence=confidence,
        profile=profile,
        provenance=provenance + ("players/bass:abstract-written-part-measurement",),
    )
