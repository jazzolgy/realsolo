"""v1.31 evidence-bounded motion tendencies derived from 131 symbolic items."""
from music_intelligence.reasoning.legend_style_core import LegendProfile, StyleTendency
from .parker_conditional_statistics import build_statistics


def build_parker_statistical_profile() -> LegendProfile:
    s = build_statistics()
    return LegendProfile(
        profile_id="legend.charlie_parker.symbolic_motion.v131",
        display_name="Charlie Parker symbolic motion prior v1.31",
        instrument_family="alto_saxophone",
        era_or_school="bebop",
        source_count=s.corpus_licks,
        tendencies=(
            StyleTendency(
                "parker131.step_motion", "step_motion", frozenset(),
                +0.10 * s.global_motion.step_share, 0.82,
                ("pedagogical_symbolic_131",),
                "small motion dominates adjacent movement",
            ),
            StyleTendency(
                "parker131.within_p4", "within_p4_motion", frozenset(),
                +0.08 * s.global_motion.within_p4_share, 0.82,
                ("pedagogical_symbolic_131",),
                "most adjacent motion remains within a perfect fourth",
            ),
            StyleTendency(
                "parker131.wide_leap_rarity", "wide_leap", frozenset(),
                -0.14 * (1.0 - s.global_motion.wide_leap_share), 0.82,
                ("pedagogical_symbolic_131",),
                "wide leaps are marked events rather than default locomotion",
            ),
            StyleTendency(
                "parker131.contrary_recovery", "contrary_recovery",
                frozenset({"after_wide_leap"}),
                +0.16 * s.wide_leap_contrary_recovery_share, 0.86,
                ("pedagogical_symbolic_131",),
                "large leaps are usually followed by contrary motion",
            ),
            StyleTendency(
                "parker131.recovery_within_p4", "recovery_within_p4",
                frozenset({"after_wide_leap"}),
                +0.14 * s.wide_leap_next_within_p4_share, 0.86,
                ("pedagogical_symbolic_131",),
                "post-leap recovery is overwhelmingly compact",
            ),
            StyleTendency(
                "parker131.terminal_hold", "structural_terminal_long_tone",
                frozenset({"phrase_late"}),
                +0.10 * s.terminal_long_tone_share, 0.78,
                ("pedagogical_symbolic_131",),
                "longer values become more plausible at structural endings",
            ),
            StyleTendency(
                "parker131.compound_span_guard", "compound_span_pressure",
                frozenset(), -0.18, 0.90,
                ("pedagogical_symbolic_131",),
                "3-4 note spans beyond an octave are exceptionally rare",
            ),
        ),
        notes=(
            "Bounded pedagogical symbolic prior. It may bias an immediate "
            "candidate but may not script future notes."
        ),
    )


PARKER_SYMBOLIC_MOTION_PROFILE = build_parker_statistical_profile()
