"""Instrument-neutral voice/staff allocation candidates.

The allocator consumes notation-facing hints.  It does not decide piano
voicings, bass line grammar, horn phrasing, or drum orchestration.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StaffProfile:
    staff_id: str
    part_id: str
    role_tags: frozenset[str] = frozenset()
    nominal_low_midi: int | None = None
    nominal_high_midi: int | None = None

    def validate(self) -> None:
        if not self.staff_id:
            raise ValueError("staff_id is required")
        if not self.part_id:
            raise ValueError("part_id is required")
        if (
            self.nominal_low_midi is not None
            and self.nominal_high_midi is not None
            and self.nominal_low_midi > self.nominal_high_midi
        ):
            raise ValueError("staff MIDI range is inverted")


@dataclass(frozen=True)
class AllocationEvidence:
    source_event_ids: tuple[str, ...]
    nominal_midi: float | None = None
    voice_role: str | None = None
    layer_role: str | None = None
    previous_staff_id: str | None = None
    preferred_staff_id: str | None = None

    def validate(self) -> None:
        if not self.source_event_ids:
            raise ValueError("allocation evidence requires source events")


@dataclass(frozen=True)
class VoiceStaffCandidate:
    staff_id: str
    voice_id: str
    cost: float
    confidence: float
    reasons: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.staff_id or not self.voice_id:
            raise ValueError("staff_id and voice_id are required")
        if self.cost < 0:
            raise ValueError("allocation cost may not be negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("allocation confidence must be within 0..1")


def allocation_candidates(
    evidence: AllocationEvidence,
    staffs: tuple[StaffProfile, ...],
) -> tuple[VoiceStaffCandidate, ...]:
    """Rank plausible staff assignments while retaining alternatives."""

    evidence.validate()
    if not staffs:
        raise ValueError("at least one staff profile is required")
    for staff in staffs:
        staff.validate()

    candidates: list[VoiceStaffCandidate] = []
    for staff in staffs:
        cost = 0.0
        reasons: list[str] = []

        if evidence.preferred_staff_id is not None:
            if staff.staff_id == evidence.preferred_staff_id:
                cost -= .30
                reasons.append("explicit notation-context staff preference")
            else:
                cost += .22

        role = evidence.voice_role or evidence.layer_role
        if role:
            if role in staff.role_tags:
                cost -= .14
                reasons.append(f"role {role} matches staff profile")
            elif staff.role_tags:
                cost += .08

        if evidence.nominal_midi is not None:
            if (
                staff.nominal_low_midi is not None
                and evidence.nominal_midi < staff.nominal_low_midi
            ):
                distance = staff.nominal_low_midi - evidence.nominal_midi
                cost += min(.75, .025 * distance)
                reasons.append("pitch lies below nominal staff range")
            if (
                staff.nominal_high_midi is not None
                and evidence.nominal_midi > staff.nominal_high_midi
            ):
                distance = evidence.nominal_midi - staff.nominal_high_midi
                cost += min(.75, .025 * distance)
                reasons.append("pitch lies above nominal staff range")

        if evidence.previous_staff_id is not None:
            if staff.staff_id == evidence.previous_staff_id:
                cost -= .06
                reasons.append("staff continuity")
            else:
                cost += .04

        cost = max(0.0, cost)
        confidence = max(0.0, min(1.0, 1.0 - cost))
        voice_label = role or "voice"
        candidate = VoiceStaffCandidate(
            staff_id=staff.staff_id,
            voice_id=f"{staff.staff_id}:{voice_label}",
            cost=cost,
            confidence=confidence,
            reasons=tuple(reasons),
            provenance=("transcribe:allocation",),
        )
        candidate.validate()
        candidates.append(candidate)

    candidates.sort(key=lambda c: (c.cost, -c.confidence, c.staff_id))
    return tuple(candidates)


def preferred_allocation(
    evidence: AllocationEvidence,
    staffs: tuple[StaffProfile, ...],
) -> VoiceStaffCandidate:
    return allocation_candidates(evidence, staffs)[0]
