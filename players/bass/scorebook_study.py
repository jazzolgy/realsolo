"""Route scorebook bass evidence into the correct practice/research track.

This prevents written funk parts from contaminating walking-bass training while
still preserving them as valuable bass-performance evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from music_intelligence.corpus.scorebooks import ScoreEvidence, ScoreEvidenceKind


class BassScorebookStudyTrack(str, Enum):
    WALKING_INSTRUCTION = "walking_instruction"
    WRITTEN_WALKING_PART = "written_walking_part"
    TWO_FEEL = "two_feel"
    FUNK_WRITTEN_PART = "funk_written_part"
    INTERPRETIVE_FUNK = "interpretive_funk"
    GENERIC = "generic"


@dataclass(frozen=True)
class BassScorebookStudyDecision:
    track: BassScorebookStudyTrack
    confidence: float
    reasons: tuple[str, ...] = ()


def classify_scorebook_bass_study(
    evidence: tuple[ScoreEvidence, ...],
) -> BassScorebookStudyDecision:
    values = [(e.kind, e.value.lower(), e.confidence) for e in evidence]
    reasons: list[str] = []

    has_written_walk = any(
        kind is ScoreEvidenceKind.WRITTEN_BASS_PART and "walk" in value
        for kind, value, _ in values
    )
    if has_written_walk:
        confidence = max(c for k,v,c in values if k is ScoreEvidenceKind.WRITTEN_BASS_PART and "walk" in v)
        reasons.append("verified written walking-bass part")
        return BassScorebookStudyDecision(
            BassScorebookStudyTrack.WRITTEN_WALKING_PART,
            confidence,
            tuple(reasons),
        )

    has_walk_instruction = any(
        kind is ScoreEvidenceKind.BASS_INSTRUCTION and "walk" in value
        for kind, value, _ in values
    )
    if has_walk_instruction:
        confidence = max(c for k,v,c in values if k is ScoreEvidenceKind.BASS_INSTRUCTION and "walk" in v)
        reasons.append("explicit walking instruction without verified written bass staff")
        return BassScorebookStudyDecision(
            BassScorebookStudyTrack.WALKING_INSTRUCTION,
            confidence,
            tuple(reasons),
        )

    has_two = any(
        kind in {ScoreEvidenceKind.FEEL_CHANGE, ScoreEvidenceKind.BASS_INSTRUCTION}
        and ("two feel" in value or "2 feel" in value or "back to 2" in value)
        for kind, value, _ in values
    )
    if has_two:
        confidence = max(c for k,v,c in values if "two feel" in v or "2 feel" in v or "back to 2" in v)
        reasons.append("explicit two-feel score evidence")
        return BassScorebookStudyDecision(
            BassScorebookStudyTrack.TWO_FEEL,
            confidence,
            tuple(reasons),
        )

    style_values = [v for k,v,_ in values if k is ScoreEvidenceKind.STYLE]
    policy_values = [v for k,v,_ in values if k is ScoreEvidenceKind.WRITTEN_PART_POLICY]
    has_written = any(
        k in {ScoreEvidenceKind.WRITTEN_PART, ScoreEvidenceKind.WRITTEN_BASS_PART}
        for k,_,_ in values
    )
    is_funk = any("funk" in v for v in style_values)

    if has_written and is_funk:
        interpretive = any(
            "freely interpreted" in v or "interpretive" in v
            for v in policy_values
        )
        confidence = max((c for _,_,c in values), default=0.0)
        if interpretive:
            reasons.append("written funk part is explicitly interpretive")
            return BassScorebookStudyDecision(
                BassScorebookStudyTrack.INTERPRETIVE_FUNK,
                confidence,
                tuple(reasons),
            )
        reasons.append("dedicated written funk bass part")
        return BassScorebookStudyDecision(
            BassScorebookStudyTrack.FUNK_WRITTEN_PART,
            confidence,
            tuple(reasons),
        )

    return BassScorebookStudyDecision(
        BassScorebookStudyTrack.GENERIC,
        max((c for _,_,c in values), default=0.0),
        ("no specialized bass-study evidence",),
    )
