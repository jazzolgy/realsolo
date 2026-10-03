"""Practical score-quality checks for rehearsal/performance use.

The goal is not to grade engraving aesthetics.  It is to surface conditions
that are likely to require human cleanup before a musician reads the part.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

from .instrument_profiles import resolve_instrument_profile, written_range_warning
from .score import ReadableScore, ScoreEvent


class QualityIssueSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ScoreQualityIssue:
    severity: QualityIssueSeverity
    code: str
    message: str
    part_id: str | None = None
    event_id: str | None = None


@dataclass(frozen=True)
class ScoreQualityReport:
    score_id: str
    issues: tuple[ScoreQualityIssue, ...]

    @property
    def has_errors(self) -> bool:
        return any(i.severity is QualityIssueSeverity.ERROR for i in self.issues)

    @property
    def needs_review(self) -> bool:
        return any(
            i.severity in {QualityIssueSeverity.WARNING, QualityIssueSeverity.ERROR}
            for i in self.issues
        )


def _written_midi(event: ScoreEvent) -> int | None:
    pitch = event.written_pitch
    if pitch is None:
        return None
    natural_pc = {
        "C": 0,
        "D": 2,
        "E": 4,
        "F": 5,
        "G": 7,
        "A": 9,
        "B": 11,
    }[pitch.step]
    return (pitch.octave + 1) * 12 + natural_pc + pitch.alter


def audit_score_for_performance(score: ReadableScore) -> ScoreQualityReport:
    """Run practical checks before exporting/handing a part to a musician."""

    score.validate()
    issues: list[ScoreQualityIssue] = []

    for part in score.parts:
        profile_name = part.profile_id or part.instrument
        profile = resolve_instrument_profile(profile_name)

        if profile is None:
            issues.append(
                ScoreQualityIssue(
                    QualityIssueSeverity.INFO,
                    "instrument-profile-missing",
                    "No notation profile is registered; using generic score behavior.",
                    part_id=part.part_id,
                )
            )
        else:
            if len(part.staff_ids) != profile.staff_count:
                issues.append(
                    ScoreQualityIssue(
                        QualityIssueSeverity.ERROR,
                        "staff-count-mismatch",
                        (
                            f"{profile.display_name} profile expects "
                            f"{profile.staff_count} staff/staves but part has "
                            f"{len(part.staff_ids)}."
                        ),
                        part_id=part.part_id,
                    )
                )

            for event in part.events:
                midi = _written_midi(event)
                if midi is None:
                    continue
                warning = written_range_warning(profile, midi)
                if warning is not None:
                    issues.append(
                        ScoreQualityIssue(
                            QualityIssueSeverity.WARNING,
                            "written-range",
                            f"{profile.display_name}: {warning}.",
                            part_id=part.part_id,
                            event_id=event.event_id,
                        )
                    )

        boundaries = sorted({
            point
            for event in part.events
            if event.written_pitch is not None or event.unpitched is not None
            for point in (event.span.onset, event.span.offset)
        })
        warned_slots: set[tuple[str, Fraction]] = set()
        for onset in boundaries[:-1]:
            by_staff: dict[str, set[str]] = {}
            for event in part.events:
                if event.kind.value != "note" or event.grace_kind is not None:
                    continue
                if event.span.onset <= onset < event.span.offset:
                    by_staff.setdefault(event.staff_id, set()).add(event.voice_id)
            for staff_id, voices in by_staff.items():
                if len(voices) <= 4:
                    continue
                slot = (staff_id, onset)
                if slot in warned_slots:
                    continue
                warned_slots.add(slot)
                issues.append(
                    ScoreQualityIssue(
                        QualityIssueSeverity.WARNING,
                        "dense-voice-stack",
                        (
                            f"{len(voices)} overlapping voices on {staff_id} at "
                            f"score beat {onset}; manual voice/layout review recommended."
                        ),
                        part_id=part.part_id,
                    )
                )

    return ScoreQualityReport(score.score_id, tuple(issues))
