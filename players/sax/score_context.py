"""Sax-owned interpretation of Shared Core score context.

Shared Core says what the score explicitly supports. This module decides what
that evidence means for sax phrase/density/interaction policy without inventing
missing score information.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from music_intelligence.corpus import ScoreContextSnapshot


class SaxScoreActivity(str, Enum):
    UNSPECIFIED = "unspecified"
    HEAD_WRITTEN = "head_written"
    WRITTEN_SOLO = "written_solo"
    WRITTEN_PART = "written_part"
    OPEN_SOLO = "open_solo"


@dataclass(frozen=True)
class SaxScorePolicyContext:
    activity: SaxScoreActivity = SaxScoreActivity.UNSPECIFIED
    style_tags: frozenset[str] = frozenset()
    rhythmic_feel: str = "unknown"
    section: str | None = None
    section_role: str | None = None
    section_changed: bool = False
    current_feel: str | None = None
    feel_change_here: str | None = None
    pending_feel_change: str | None = None
    phrase_boundary_before: bool = False
    phrase_boundary_after: bool = False
    density_delta: float = 0.0
    space_bias: float = 0.0
    phrase_start_bias: float = 0.0
    phrase_end_bias: float = 0.0
    transition_bias: float = 0.0
    confidence: float = 1.0
    reasons: tuple[str, ...] = ()


def _activity(snapshot: ScoreContextSnapshot) -> SaxScoreActivity:
    if snapshot.written_melody_active:
        return SaxScoreActivity.HEAD_WRITTEN

    solo = (snapshot.solo_indication or "").strip().lower()
    if solo:
        if "written" in solo or "notated" in solo:
            return SaxScoreActivity.WRITTEN_SOLO
        return SaxScoreActivity.OPEN_SOLO

    written = (snapshot.written_part_role or "").strip().lower()
    if written:
        if "solo" in written and ("written" in written or "notated" in written):
            return SaxScoreActivity.WRITTEN_SOLO
        return SaxScoreActivity.WRITTEN_PART

    return SaxScoreActivity.UNSPECIFIED


def _style_tags(styles: tuple[str, ...]) -> frozenset[str]:
    joined = " ".join(styles).lower()
    tags: set[str] = set()
    for token in (
        "bebop", "swing", "latin", "bossa", "funk", "ballad",
        "even 8", "waltz", "afro", "medium", "fast", "up",
    ):
        if token in joined:
            tags.add(token.replace(" ", "_"))
    return frozenset(tags)


def interpret_score_context(
    snapshot: ScoreContextSnapshot,
    *,
    previous: ScoreContextSnapshot | None = None,
) -> SaxScorePolicyContext:
    tags = _style_tags(snapshot.style)
    reasons: list[str] = []
    density = 0.0
    space = 0.0
    start_bias = 0.0
    end_bias = 0.0
    transition = 0.0

    feel_candidates = {
        "swing": "swing" in tags,
        "latin": "latin" in tags or "bossa" in tags or "afro" in tags,
        "straight": "even_8" in tags,
        "funk": "funk" in tags,
    }
    active_feels = [name for name, yes in feel_candidates.items() if yes]
    rhythmic_feel = (
        active_feels[0] if len(active_feels) == 1
        else "mixed" if len(active_feels) > 1
        else "unknown"
    )

    if "bebop" in tags:
        density += .10
        reasons.append("score style supports bebop-density vocabulary")
    if "fast" in tags or "up" in tags:
        density += .05
    if "ballad" in tags:
        density -= .18
        space += .12
        reasons.append("ballad style favors space and longer occupancy")

    if snapshot.phrase_boundary_before:
        start_bias += .30
        reasons.append("explicit score phrase start")
    if snapshot.phrase_boundary_after:
        end_bias += .34
        space += .12
        reasons.append("explicit score phrase end")

    if snapshot.feel_change_here:
        transition += .36
        end_bias += .10
        reasons.append("explicit feel change occurs here")
    elif snapshot.pending_feel_change:
        transition += .24
        end_bias += .08
        space += .06
        reasons.append("explicit upcoming feel change")

    section_changed = bool(
        previous is not None
        and previous.section is not None
        and snapshot.section is not None
        and previous.section != snapshot.section
    )
    if section_changed:
        start_bias += .16
        transition += .10
        reasons.append("explicit section changed")

    activity = _activity(snapshot)
    if activity is SaxScoreActivity.HEAD_WRITTEN:
        reasons.append("written head melody is active")
    elif activity is SaxScoreActivity.WRITTEN_SOLO:
        reasons.append("written solo material is active")
    elif activity is SaxScoreActivity.WRITTEN_PART:
        reasons.append("written part is active")
    elif activity is SaxScoreActivity.OPEN_SOLO:
        reasons.append("score explicitly opens improvisation")

    return SaxScorePolicyContext(
        activity=activity,
        style_tags=tags,
        rhythmic_feel=rhythmic_feel,
        section=snapshot.section,
        section_role=snapshot.section_role,
        section_changed=section_changed,
        current_feel=snapshot.current_feel,
        feel_change_here=snapshot.feel_change_here,
        pending_feel_change=snapshot.pending_feel_change,
        phrase_boundary_before=snapshot.phrase_boundary_before,
        phrase_boundary_after=snapshot.phrase_boundary_after,
        density_delta=max(-1.0, min(1.0, density)),
        space_bias=max(0.0, min(1.0, space)),
        phrase_start_bias=max(0.0, min(1.0, start_bias)),
        phrase_end_bias=max(0.0, min(1.0, end_bias)),
        transition_bias=max(0.0, min(1.0, transition)),
        confidence=snapshot.confidence,
        reasons=tuple(reasons),
    )
