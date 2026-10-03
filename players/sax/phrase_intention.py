"""Causal phrase-level intention for the Sax Player.

The intention shapes only the *next* event family, duration, target emphasis,
and space. It never precomposes or stores a future note sequence.
"""
from __future__ import annotations

from dataclasses import dataclass
from music_intelligence.harmony.scale_linear_core import LinearRouteKind


@dataclass(frozen=True)
class SaxPhraseIntention:
    phase: str
    duration_beats: float
    rest_bias: float
    route_biases: dict[LinearRouteKind,float]
    register_direction: int = 0
    target_emphasis: float = 0.0
    reasons: tuple[str,...] = ()


@dataclass
class SaxPhraseIntentionMemory:
    last_phase: str = ""
    recent_event_count: int = 0
    held_ticks_remaining: int = 0

    def reset(self) -> None:
        self.last_phase=""
        self.recent_event_count=0
        self.held_ticks_remaining=0

    def consume_hold(self) -> bool:
        if self.held_ticks_remaining <= 0:
            return False
        self.held_ticks_remaining -= 1
        return True

    def commit_duration(self, duration_beats: float, *, decision_step_beats: float=.5) -> None:
        extra=max(0.0,duration_beats-decision_step_beats)
        self.held_ticks_remaining=max(0,int(round(extra/decision_step_beats)))
        self.recent_event_count += 1


def choose_sax_phrase_intention(
    *,
    phrase_maturity: float,
    beat_in_bar: float,
    section: str,
    tension: float,
    previous_pitch_midi: int | None,
    recent_event_count: int,
) -> SaxPhraseIntention:
    """Choose one causal phrase intention from current musical context."""

    m=max(0.0,min(1.0,phrase_maturity))
    beat=beat_in_bar%4.0
    tension=max(0.0,min(1.0,tension))

    if m < .18:
        phase="attack"
        duration=.5 if beat in {0.5,1.5,2.5,3.5} else 1.0
        rest=.03
        biases={
            LinearRouteKind.DIATONIC_PASSING:.10,
            LinearRouteKind.ARPEGGIO_FRAGMENT:.06,
            LinearRouteKind.CHORDAL:-.04,
            LinearRouteKind.APPROACH:.05,
        }
        reg=1
        target=.25
        reasons=("establish phrase direction without chord-tone anchoring",)
    elif m < .62:
        phase="develop"
        duration=.5
        rest=.02 if recent_event_count%4 else .08
        biases={
            LinearRouteKind.DIATONIC_PASSING:.14,
            LinearRouteKind.CHROMATIC_PASSING:.12,
            LinearRouteKind.APPROACH:.15,
            LinearRouteKind.ENCLOSURE:.13,
            LinearRouteKind.CHORDAL:-.10,
            LinearRouteKind.COMMON_TONE:-.04,
        }
        reg=1 if tension>=.45 else 0
        target=.55
        reasons=("develop line through passing/approach/enclosure motion",)
    elif m < .86:
        phase="target"
        duration=.5 if beat < 3.0 else 1.0
        rest=.05
        biases={
            LinearRouteKind.APPROACH:.18,
            LinearRouteKind.ENCLOSURE:.19,
            LinearRouteKind.ANTICIPATION:.16,
            LinearRouteKind.CHORDAL:.02,
            LinearRouteKind.DIATONIC_PASSING:.07,
        }
        reg=0
        target=.90
        reasons=("aim current motion toward guide-tone arrival",)
    else:
        phase="release"
        duration=1.5 if beat <= 2.0 else 1.0
        rest=.72
        biases={
            LinearRouteKind.CHORDAL:.07,
            LinearRouteKind.COMMON_TONE:.10,
            LinearRouteKind.ANTICIPATION:.08,
            LinearRouteKind.APPROACH:.04,
            LinearRouteKind.ENCLOSURE:-.08,
            LinearRouteKind.CHROMATIC_PASSING:-.06,
        }
        reg=-1
        target=.75
        reasons=("release phrase with space or stable arrival",)

    if section.upper()=="B" and phase in {"develop","target"}:
        biases=dict(biases)
        biases[LinearRouteKind.CHROMATIC_PASSING]=biases.get(LinearRouteKind.CHROMATIC_PASSING,0)+.04
        biases[LinearRouteKind.ENCLOSURE]=biases.get(LinearRouteKind.ENCLOSURE,0)+.04

    return SaxPhraseIntention(
        phase=phase,
        duration_beats=duration,
        rest_bias=rest,
        route_biases=biases,
        register_direction=reg,
        target_emphasis=target,
        reasons=reasons,
    )
