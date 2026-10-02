"""Parker conditional motion prior derived from bounded symbolic evidence."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from music_intelligence.reasoning.legend_style_core import LegendProfile, StyleTendency


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
    path = Path(__file__).with_name("data") / "conditional_motion_stats.json"
    return ParkerConditionalStatistics.from_dict(json.loads(path.read_text(encoding="utf-8")))


def build_symbolic_motion_profile() -> LegendProfile:
    s = build_statistics()
    return LegendProfile(
        profile_id="legend.charlie_parker.symbolic_motion",
        display_name="Charlie Parker symbolic motion prior",
        instrument_family="alto_saxophone",
        era_or_school="bebop",
        source_count=s.corpus_licks,
        tendencies=(
            StyleTendency("parker.step_motion", "step_motion", frozenset(),
                          +.10 * s.global_motion.step_share, .82, ("pedagogical_symbolic_131",),
                          "small motion dominates adjacent movement"),
            StyleTendency("parker.within_p4", "within_p4_motion", frozenset(),
                          +.08 * s.global_motion.within_p4_share, .82, ("pedagogical_symbolic_131",),
                          "most adjacent motion remains within a perfect fourth"),
            StyleTendency("parker.wide_leap_rarity", "wide_leap", frozenset(),
                          -.14 * (1.0 - s.global_motion.wide_leap_share), .82,
                          ("pedagogical_symbolic_131",), "wide leaps are marked events"),
            StyleTendency("parker.contrary_recovery", "contrary_recovery",
                          frozenset({"after_wide_leap"}),
                          +.16 * s.wide_leap_contrary_recovery_share, .86,
                          ("pedagogical_symbolic_131",), "large leaps usually recover contrary"),
            StyleTendency("parker.recovery_within_p4", "recovery_within_p4",
                          frozenset({"after_wide_leap"}),
                          +.14 * s.wide_leap_next_within_p4_share, .86,
                          ("pedagogical_symbolic_131",), "post-leap recovery is compact"),
            StyleTendency("parker.terminal_hold", "structural_terminal_long_tone",
                          frozenset({"phrase_late"}),
                          +.10 * s.terminal_long_tone_share, .78,
                          ("pedagogical_symbolic_131",), "long values become plausible at endings"),
            StyleTendency("parker.compound_span_guard", "compound_span_pressure",
                          frozenset(), -.18, .90, ("pedagogical_symbolic_131",),
                          "short compound spans are exceptional"),
        ),
        notes="Bounded symbolic prior; immediate-candidate bias only.",
    )


PARKER_SYMBOLIC_MOTION_PROFILE = build_symbolic_motion_profile()
