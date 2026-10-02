"""High-resolution score/performance alignment analysis.

This module turns an already-aligned score + performance note stream into
microtiming evidence without assuming a fixed global tempo. Expected note times
are interpolated from local downbeat anchors so tempo drift and rubato are
separated from within-beat placement.

It intentionally does not generate music and does not alter the online commit
contract. It is an offline research utility whose output may later become
bounded runtime priors after evidence review.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isclose
from statistics import mean, median
from typing import Sequence


@dataclass(frozen=True)
class ScoreNote:
    pitch_midi: int
    score_beat: float
    duration_beats: float
    note_id: str | None = None


@dataclass(frozen=True)
class PerformanceNote:
    pitch_midi: int
    onset_s: float
    offset_s: float
    note_id: str | None = None

    @property
    def duration_s(self) -> float:
        return max(0.0, self.offset_s - self.onset_s)


@dataclass(frozen=True)
class DownbeatAnchor:
    score_beat: float
    time_s: float


@dataclass(frozen=True)
class NoteAlignment:
    score_index: int
    performance_index: int
    pitch_midi: int
    score_beat: float
    expected_onset_s: float
    performed_onset_s: float
    onset_offset_ms: float
    expected_duration_s: float
    performed_duration_s: float
    duration_ratio: float | None
    metric_class: str


@dataclass(frozen=True)
class SwingPair:
    score_beat: float
    first_ioi_s: float
    second_ioi_s: float
    ratio: float


@dataclass(frozen=True)
class AlignmentSummary:
    matched_notes: int
    score_notes: int
    performance_notes: int
    match_coverage: float
    mean_offset_ms: float
    median_offset_ms: float
    mean_abs_offset_ms: float
    metric_offset_ms: dict[str, float]
    mean_duration_ratio: float | None
    swing_pair_count: int
    median_swing_ratio: float | None


class LocalBeatTimeMap:
    """Piecewise-linear score-beat to performance-time mapping."""

    def __init__(self, anchors: Sequence[DownbeatAnchor]):
        if len(anchors) < 2:
            raise ValueError("at least two downbeat anchors are required")
        ordered = tuple(sorted(anchors, key=lambda x: x.score_beat))
        for a, b in zip(ordered, ordered[1:]):
            if b.score_beat <= a.score_beat:
                raise ValueError("score beats must be strictly increasing")
            if b.time_s <= a.time_s:
                raise ValueError("anchor times must be strictly increasing")
        self.anchors = ordered

    def time_at(self, score_beat: float) -> float:
        a, b = self._bracket(score_beat)
        frac = (score_beat - a.score_beat) / (b.score_beat - a.score_beat)
        return a.time_s + frac * (b.time_s - a.time_s)

    def seconds_per_beat_at(self, score_beat: float) -> float:
        a, b = self._bracket(score_beat)
        return (b.time_s - a.time_s) / (b.score_beat - a.score_beat)

    def _bracket(self, score_beat: float) -> tuple[DownbeatAnchor, DownbeatAnchor]:
        anchors = self.anchors
        if score_beat <= anchors[0].score_beat:
            return anchors[0], anchors[1]
        if score_beat >= anchors[-1].score_beat:
            return anchors[-2], anchors[-1]
        for a, b in zip(anchors, anchors[1:]):
            if a.score_beat <= score_beat <= b.score_beat:
                return a, b
        raise RuntimeError("unreachable beat-map bracket")


def _metric_class(score_beat: float, tol: float = 1e-4) -> str:
    phase = score_beat % 1.0
    if isclose(phase, 0.0, abs_tol=tol) or isclose(phase, 1.0, abs_tol=tol):
        return "beat"
    if isclose(phase, 0.5, abs_tol=tol):
        return "eighth_upbeat"
    if isclose(phase, 1 / 3, abs_tol=tol) or isclose(phase, 2 / 3, abs_tol=tol):
        return "triplet"
    if isclose(phase, 0.25, abs_tol=tol) or isclose(phase, 0.75, abs_tol=tol):
        return "sixteenth_grid"
    return "other"


def align_note_sequences(
    score_notes: Sequence[ScoreNote],
    performance_notes: Sequence[PerformanceNote],
) -> tuple[tuple[int, int], ...]:
    if not score_notes or not performance_notes:
        return ()

    if all(n.note_id is not None for n in score_notes) and all(n.note_id is not None for n in performance_notes):
        perf_by_id = {n.note_id: i for i, n in enumerate(performance_notes)}
        pairs = []
        last = -1
        for i, note in enumerate(score_notes):
            j = perf_by_id.get(note.note_id)
            if j is not None and j > last and performance_notes[j].pitch_midi == note.pitch_midi:
                pairs.append((i, j))
                last = j
        if pairs:
            return tuple(pairs)

    n, m = len(score_notes), len(performance_notes)
    gap = 1.0
    mismatch = 2.5
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    bt = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i * gap
        bt[i][0] = "up"
    for j in range(1, m + 1):
        dp[0][j] = j * gap
        bt[0][j] = "left"

    for i in range(1, n + 1):
        sp = score_notes[i - 1].pitch_midi
        for j in range(1, m + 1):
            pp = performance_notes[j - 1].pitch_midi
            diag_cost = dp[i - 1][j - 1] + (0.0 if sp == pp else mismatch)
            up_cost = dp[i - 1][j] + gap
            left_cost = dp[i][j - 1] + gap
            best = min(diag_cost, up_cost, left_cost)
            dp[i][j] = best
            bt[i][j] = "diag" if best == diag_cost else ("up" if best == up_cost else "left")

    pairs: list[tuple[int, int]] = []
    i, j = n, m
    while i > 0 or j > 0:
        move = bt[i][j]
        if move == "diag":
            if score_notes[i - 1].pitch_midi == performance_notes[j - 1].pitch_midi:
                pairs.append((i - 1, j - 1))
            i -= 1
            j -= 1
        elif move == "up":
            i -= 1
        else:
            j -= 1
    pairs.reverse()
    return tuple(pairs)


def analyze_aligned_performance(
    score_notes: Sequence[ScoreNote],
    performance_notes: Sequence[PerformanceNote],
    beat_map: LocalBeatTimeMap,
) -> tuple[tuple[NoteAlignment, ...], tuple[SwingPair, ...], AlignmentSummary]:
    pairs = align_note_sequences(score_notes, performance_notes)
    aligned: list[NoteAlignment] = []
    by_score_index: dict[int, NoteAlignment] = {}

    for si, pi in pairs:
        s = score_notes[si]
        p = performance_notes[pi]
        expected = beat_map.time_at(s.score_beat)
        spb = beat_map.seconds_per_beat_at(s.score_beat)
        expected_duration = max(0.0, s.duration_beats * spb)
        ratio = p.duration_s / expected_duration if expected_duration > 1e-9 else None
        item = NoteAlignment(
            score_index=si,
            performance_index=pi,
            pitch_midi=s.pitch_midi,
            score_beat=s.score_beat,
            expected_onset_s=expected,
            performed_onset_s=p.onset_s,
            onset_offset_ms=(p.onset_s - expected) * 1000.0,
            expected_duration_s=expected_duration,
            performed_duration_s=p.duration_s,
            duration_ratio=ratio,
            metric_class=_metric_class(s.score_beat),
        )
        aligned.append(item)
        by_score_index[si] = item

    swings: list[SwingPair] = []
    for i in range(len(score_notes) - 2):
        a, b, c = score_notes[i:i + 3]
        base = round(a.score_beat)
        if not (
            isclose(a.score_beat, base, abs_tol=1e-4)
            and isclose(b.score_beat, base + 0.5, abs_tol=1e-4)
            and isclose(c.score_beat, base + 1.0, abs_tol=1e-4)
        ):
            continue
        if i not in by_score_index or i + 1 not in by_score_index or i + 2 not in by_score_index:
            continue
        t0 = by_score_index[i].performed_onset_s
        t1 = by_score_index[i + 1].performed_onset_s
        t2 = by_score_index[i + 2].performed_onset_s
        first, second = t1 - t0, t2 - t1
        if first > 0 and second > 0:
            swings.append(SwingPair(a.score_beat, first, second, first / second))

    offsets = [a.onset_offset_ms for a in aligned]
    duration_ratios = [a.duration_ratio for a in aligned if a.duration_ratio is not None]
    metric: dict[str, list[float]] = {}
    for a in aligned:
        metric.setdefault(a.metric_class, []).append(a.onset_offset_ms)

    denom = max(len(score_notes), len(performance_notes), 1)
    summary = AlignmentSummary(
        matched_notes=len(aligned),
        score_notes=len(score_notes),
        performance_notes=len(performance_notes),
        match_coverage=len(aligned) / denom,
        mean_offset_ms=mean(offsets) if offsets else 0.0,
        median_offset_ms=median(offsets) if offsets else 0.0,
        mean_abs_offset_ms=mean(abs(x) for x in offsets) if offsets else 0.0,
        metric_offset_ms={k: mean(v) for k, v in metric.items()},
        mean_duration_ratio=mean(duration_ratios) if duration_ratios else None,
        swing_pair_count=len(swings),
        median_swing_ratio=median(s.ratio for s in swings) if swings else None,
    )
    return tuple(aligned), tuple(swings), summary
