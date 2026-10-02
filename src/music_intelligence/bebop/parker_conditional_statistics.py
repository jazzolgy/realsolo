"""v1.31 aggregate Parker-style conditional motion statistics.

The committed aggregate is derived from the exact-131 pedagogical symbolic
corpus. Raw copyrighted source material is intentionally not committed to this
public repository.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass(frozen=True)
class MotionStats:
    transitions: int
    step_share: float
    within_p4_share: float
    wide_leap_share: float
    compound_leap_share: float
    mean_abs_interval: float


@dataclass(frozen=True)
class ParkerConditionalStatistics:
    corpus_licks: int
    global_motion: MotionStats
    phase_motion: dict[str, MotionStats]
    family_motion: dict[str, MotionStats]
    terminal_long_tone_share: float
    terminal_duration_mean_eighths: float
    internal_duration_mean_eighths: float
    wide_leap_count_with_followup: int
    wide_leap_contrary_recovery_share: float
    wide_leap_next_within_p4_share: float
    three_note_span_gt_octave_share: float
    four_note_span_gt_octave_share: float

    @classmethod
    def from_dict(cls, p: dict) -> "ParkerConditionalStatistics":
        return cls(
            corpus_licks=int(p["corpus_licks"]),
            global_motion=MotionStats(**p["global_motion"]),
            phase_motion={k: MotionStats(**v) for k, v in p["phase_motion"].items()},
            family_motion={k: MotionStats(**v) for k, v in p["family_motion"].items()},
            terminal_long_tone_share=float(p["terminal_long_tone_share"]),
            terminal_duration_mean_eighths=float(p["terminal_duration_mean_eighths"]),
            internal_duration_mean_eighths=float(p["internal_duration_mean_eighths"]),
            wide_leap_count_with_followup=int(p["wide_leap_count_with_followup"]),
            wide_leap_contrary_recovery_share=float(p["wide_leap_contrary_recovery_share"]),
            wide_leap_next_within_p4_share=float(p["wide_leap_next_within_p4_share"]),
            three_note_span_gt_octave_share=float(p["three_note_span_gt_octave_share"]),
            four_note_span_gt_octave_share=float(p["four_note_span_gt_octave_share"]),
        )


def build_statistics() -> ParkerConditionalStatistics:
    path = Path(__file__).with_name("data") / "parker_symbolic_conditional_stats_v131.json"
    return ParkerConditionalStatistics.from_dict(
        json.loads(path.read_text(encoding="utf-8"))
    )
