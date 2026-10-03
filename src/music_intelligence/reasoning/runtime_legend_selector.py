"""Runtime legend selection policy over canonical Shared Legend resources.

This module is a consumer/policy adapter. Legend profiles and vocabulary data
remain owned by music_intelligence.legends and runtime_legend_resources.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from music_intelligence.legends.interfaces import LegendProfileView, VocabularyProvider
from music_intelligence.reasoning.legend_style_core import LegendBlend
from .runtime_legend_resources import legend_runtime_resources


@dataclass(frozen=True)
class LegendRuntimeChoice:
    player_id: str
    legend_id: str
    profile_view: LegendProfileView
    vocabulary_provider: VocabularyProvider
    weight: float
    reason: str
    profile_active: bool

    def validate(self) -> None:
        if not self.player_id or not self.legend_id:
            raise ValueError("player_id and legend_id are required")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError("legend weight must be within 0..1")


def _choice(player_id: str, legend_id: str, weight: float, reason: str) -> LegendRuntimeChoice:
    resources=legend_runtime_resources(legend_id)
    item=LegendRuntimeChoice(
        player_id=player_id,
        legend_id=legend_id,
        profile_view=resources.profile_view,
        vocabulary_provider=resources.vocabulary_provider,
        weight=weight,
        reason=reason,
        profile_active=resources.profile_available,
    )
    item.validate()
    return item


def select_runtime_legends(
    *,
    style_tags: tuple[str,...],
    overrides: Mapping[str,str] | None=None,
) -> tuple[LegendRuntimeChoice,...]:
    tags={x.strip().lower().replace("-","_") for x in style_tags}
    overrides=overrides or {}
    out: list[LegendRuntimeChoice]=[]

    for player_id,legend_id in overrides.items():
        try:
            out.append(_choice(player_id,str(legend_id),.55,"explicit session legend override"))
        except KeyError:
            continue

    selected={x.player_id for x in out}
    if "sax" not in selected and "bebop" in tags:
        resources=legend_runtime_resources("charlie_parker")
        if resources.profile_available:
            out.append(_choice(
                "sax","charlie_parker",.24,
                "bebop sax context; conservative legend prior",
            ))

    if (
        "bass" not in selected
        and {"interactive_trio","modern_jazz_trio"}.intersection(tags)
    ):
        resources=legend_runtime_resources("scott_lafaro")
        if resources.profile_available:
            out.append(_choice(
                "bass","scott_lafaro",.24,
                "interactive modern-trio context",
            ))

    return tuple(out)


def select_showcase_legends(*,style_tags: tuple[str,...]) -> tuple[LegendRuntimeChoice,...]:
    out=[]
    for player_id,legend_id in (
        ("sax","charlie_parker"),
        ("piano","bill_evans"),
        ("bass","scott_lafaro"),
    ):
        resources=legend_runtime_resources(legend_id)
        # Showcase may expose source-grounded vocabulary even when the profile
        # has no promoted tendencies; legend_blend_for remains inactive then.
        if resources.profile_available or resources.vocabulary_available(
            target_instrument=player_id
        ):
            out.append(_choice(
                player_id,legend_id,1.0,
                "legend showcase: canonical promoted resources",
            ))
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
    if choice is None or not choice.profile_active:
        return None
    blend=choice.profile_view.blend(choice.weight)
    blend.validate()
    return blend
