"""Contextual runtime selection for promoted Legend Intelligence.

Legend research is a narrow soft-prior layer, never the generic jazz brain.
This selector activates only source-grounded profiles that fit the current
instrument/style context, or an explicit session override.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from music_intelligence.legends.interfaces import LegendProfileView, VocabularyProvider
from music_intelligence.legends.parker import PARKER_PROFILE_VIEW, PARKER_VOCABULARY_INDEX
from music_intelligence.legends.bill_evans import BILL_EVANS_PROFILE_VIEW, BILL_EVANS_VOCABULARY_INDEX
from music_intelligence.legends.scott_lafaro import SCOTT_LAFARO_PROFILE_VIEW, SCOTT_LAFARO_VOCABULARY_INDEX
from music_intelligence.reasoning.legend_style_core import LegendBlend


@dataclass(frozen=True)
class LegendRuntimeChoice:
    player_id: str
    legend_id: str
    profile_view: LegendProfileView
    vocabulary_provider: VocabularyProvider
    weight: float
    reason: str

    def validate(self) -> None:
        if not self.player_id or not self.legend_id:
            raise ValueError("player_id and legend_id are required")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError("legend weight must be within 0..1")


_REGISTRY = {
    "charlie_parker": (PARKER_PROFILE_VIEW, PARKER_VOCABULARY_INDEX),
    "bill_evans": (BILL_EVANS_PROFILE_VIEW, BILL_EVANS_VOCABULARY_INDEX),
    "scott_lafaro": (SCOTT_LAFARO_PROFILE_VIEW, SCOTT_LAFARO_VOCABULARY_INDEX),
}


def _usable(view: LegendProfileView) -> bool:
    profiles=view.weighted_profiles()
    return any(profile.source_count > 0 and profile.tendencies for profile,_ in profiles)


def _explicit_choice(player_id: str, legend_id: str) -> LegendRuntimeChoice | None:
    pair=_REGISTRY.get(legend_id)
    if pair is None:
        return None
    view,provider=pair
    if not _usable(view):
        return None
    return LegendRuntimeChoice(
        player_id=player_id,
        legend_id=legend_id,
        profile_view=view,
        vocabulary_provider=provider,
        weight=.55,
        reason="explicit session legend override",
    )


def select_runtime_legends(
    *,
    style_tags: tuple[str,...],
    overrides: Mapping[str,str] | None = None,
) -> tuple[LegendRuntimeChoice,...]:
    """Select bounded contextual legend priors.

    Generic jazz does not automatically become a named-musician imitation.
    Automatic choices are conservative and require a strong contextual match.
    """

    tags={x.strip().lower().replace("-","_") for x in style_tags}
    overrides=overrides or {}
    out=[]

    for player_id,legend_id in overrides.items():
        choice=_explicit_choice(player_id,str(legend_id))
        if choice is not None:
            out.append(choice)

    selected_players={x.player_id for x in out}

    # Parker is a well-supported bebop linear-language reference. A generic
    # tenor-sax bebop session may borrow a small soft prior without claiming
    # Parker imitation.
    if "sax" not in selected_players and "bebop" in tags and _usable(PARKER_PROFILE_VIEW):
        out.append(LegendRuntimeChoice(
            player_id="sax",
            legend_id="charlie_parker",
            profile_view=PARKER_PROFILE_VIEW,
            vocabulary_provider=PARKER_VOCABULARY_INDEX,
            weight=.24,
            reason="bebop sax context; conservative cross-sax legend prior",
        ))

    # LaFaro is not a generic walking-bass default. Activate automatically only
    # when the session explicitly identifies an interactive modern-trio context.
    if (
        "bass" not in selected_players
        and {"interactive_trio","modern_jazz_trio"}.intersection(tags)
        and _usable(SCOTT_LAFARO_PROFILE_VIEW)
    ):
        out.append(LegendRuntimeChoice(
            player_id="bass",
            legend_id="scott_lafaro",
            profile_view=SCOTT_LAFARO_PROFILE_VIEW,
            vocabulary_provider=SCOTT_LAFARO_VOCABULARY_INDEX,
            weight=.24,
            reason="interactive modern-trio context",
        ))

    # Bill Evans profile is currently evidence-gated and empty. The selector
    # deliberately does not activate an empty profile from reputation alone.

    for item in out:
        item.validate()
    return tuple(out)


def legend_choice_for(
    choices: tuple[LegendRuntimeChoice,...],
    player_id: str,
) -> LegendRuntimeChoice | None:
    return next((x for x in choices if x.player_id==player_id),None)


def legend_blend_for(
    choices: tuple[LegendRuntimeChoice,...],
    player_id: str,
) -> LegendBlend | None:
    choice=legend_choice_for(choices,player_id)
    if choice is None:
        return None
    blend=choice.profile_view.blend(choice.weight)
    blend.validate()
    return blend
