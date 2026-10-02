"""Practical validation for live chord charts.

This checks whether written navigation/form symbols are internally usable.
It does not execute the form; authoritative playback traversal belongs to
Shared Core (CCR-TRANSCRIBE-002).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .chord_chart import ChordChart, MeasureRepeatKind, NavigationMark, resolved_measure_chords


class ChartIssueSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ChordChartIssue:
    severity: ChartIssueSeverity
    code: str
    message: str
    measure_number: int | None = None


@dataclass(frozen=True)
class ChordChartAudit:
    chart_id: str
    issues: tuple[ChordChartIssue, ...]

    @property
    def has_errors(self) -> bool:
        return any(i.severity is ChartIssueSeverity.ERROR for i in self.issues)

    @property
    def needs_review(self) -> bool:
        return any(
            i.severity in {ChartIssueSeverity.WARNING, ChartIssueSeverity.ERROR}
            for i in self.issues
        )


def audit_chord_chart(chart: ChordChart) -> ChordChartAudit:
    """Find malformed navigation/repeat notation before live use."""

    chart.validate()
    issues: list[ChordChartIssue] = []

    marks: dict[NavigationMark, list[int]] = {mark: [] for mark in NavigationMark}
    repeat_depth = 0
    has_any_repeat = False

    for measure in chart.measures:
        for mark in measure.navigation_marks:
            marks[mark].append(measure.number)

        if measure.repeat_start:
            repeat_depth += 1
            has_any_repeat = True
        if measure.repeat_end:
            has_any_repeat = True
            if repeat_depth == 0:
                issues.append(
                    ChordChartIssue(
                        ChartIssueSeverity.WARNING,
                        "repeat-end-without-start",
                        "Repeat end appears without an active repeat start.",
                        measure.number,
                    )
                )
            else:
                repeat_depth -= 1

        if measure.ending_numbers and not has_any_repeat:
            issues.append(
                ChordChartIssue(
                    ChartIssueSeverity.WARNING,
                    "ending-without-repeat",
                    "Numbered ending appears before any repeat structure.",
                    measure.number,
                )
            )

        if measure.repeat_shorthand is not MeasureRepeatKind.NONE:
            try:
                resolved_measure_chords(chart, measure.number)
            except ValueError as exc:
                issues.append(
                    ChordChartIssue(
                        ChartIssueSeverity.ERROR,
                        "invalid-measure-repeat",
                        str(exc),
                        measure.number,
                    )
                )

    if repeat_depth:
        issues.append(
            ChordChartIssue(
                ChartIssueSeverity.WARNING,
                "unclosed-repeat",
                "One or more repeat starts have no matching repeat end.",
            )
        )

    if marks[NavigationMark.DS] and not marks[NavigationMark.SEGNO]:
        issues.append(
            ChordChartIssue(
                ChartIssueSeverity.ERROR,
                "ds-without-segno",
                "D.S. is present but no Segno target exists.",
                marks[NavigationMark.DS][0],
            )
        )

    if marks[NavigationMark.TO_CODA] and not marks[NavigationMark.CODA]:
        issues.append(
            ChordChartIssue(
                ChartIssueSeverity.ERROR,
                "to-coda-without-coda",
                "To Coda is present but no Coda target exists.",
                marks[NavigationMark.TO_CODA][0],
            )
        )

    if len(marks[NavigationMark.SEGNO]) > 1:
        issues.append(
            ChordChartIssue(
                ChartIssueSeverity.WARNING,
                "multiple-segno",
                "Multiple Segno targets require explicit disambiguation.",
            )
        )

    if len(marks[NavigationMark.CODA]) > 1:
        issues.append(
            ChordChartIssue(
                ChartIssueSeverity.WARNING,
                "multiple-coda",
                "Multiple Coda targets require explicit disambiguation.",
            )
        )

    return ChordChartAudit(chart.chart_id, tuple(issues))
