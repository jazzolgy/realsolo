"""Bass-specific consumption of shared scorebook evidence.

Shared Core owns the evidence schema. This module only translates explicit
scorebook evidence into soft bass-performance pressure.

Important:
- evidence never injects copied written notes into generation;
- written-part availability is a comparison/evaluation signal, not a note source;
- feel/instruction confidence scales its musical influence.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.corpus.score_context import ScoreContextSnapshot
from music_intelligence.corpus.scorebooks import ScoreEvidence, ScoreEvidenceKind


@dataclass(frozen=True)
class BassWrittenPartPrior:
    root_preference: float = 0.0
    scalar_preference: float = 0.0
    chromatic_preference: float = 0.0
    reversal_preference: float = 0.0
    register_center_midi: float | None = None


@dataclass(frozen=True)
class BassScoreEvidenceDirective:
    preferred_mode: str | None = None
    walking_pressure: float = 0.0
    two_feel_pressure: float = 0.0
    written_part_available: bool = False
    written_part_prior: BassWrittenPartPrior | None = None
    confidence: float = 0.0
    provenance: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


def derive_bass_score_evidence(
    evidence: tuple[ScoreEvidence, ...],
) -> BassScoreEvidenceDirective:
    walking = 0.0
    two_feel = 0.0
    written = False
    confidences: list[float] = []
    provenance: list[str] = []
    reasons: list[str] = []

    for item in evidence:
        item.validate()
        value = item.value.lower().strip()
        confidences.append(item.confidence)
        provenance.extend(item.provenance)

        if item.kind is ScoreEvidenceKind.FEEL_CHANGE:
            if "two feel" in value or "back to 2" in value or "2 feel" in value:
                two_feel += item.confidence
                reasons.append(f"score feel evidence: {item.value}")
            if "in four" in value or "4 feel" in value or "walking" in value:
                walking += item.confidence
                reasons.append(f"score feel evidence: {item.value}")

        if item.kind is ScoreEvidenceKind.BASS_INSTRUCTION:
            if "walk" in value or "in four" in value:
                walking += item.confidence
                reasons.append(f"bass instruction: {item.value}")
            if "two feel" in value or "2 feel" in value:
                two_feel += item.confidence
                reasons.append(f"bass instruction: {item.value}")

        if item.kind in {
            ScoreEvidenceKind.WRITTEN_PART,
            ScoreEvidenceKind.WRITTEN_BASS_PART,
        }:
            written = True
            if "walk" in value:
                walking += .5 * item.confidence
                reasons.append(f"written bass-part evidence: {item.value}")

    walking = min(1.0, walking)
    two_feel = min(1.0, two_feel)
    preferred = None
    if walking > two_feel + .10:
        preferred = "walking"
    elif two_feel > walking + .10:
        preferred = "two_feel"

    confidence = max(confidences) if confidences else 0.0
    return BassScoreEvidenceDirective(
        preferred_mode=preferred,
        walking_pressure=walking,
        two_feel_pressure=two_feel,
        written_part_available=written,
        confidence=confidence,
        provenance=tuple(dict.fromkeys(provenance)),
        reasons=tuple(reasons),
    )


def evidence_candidate_score(
    directive: BassScoreEvidenceDirective,
    *,
    mode: str,
    harmonic_role: str,
    metric_role: str,
) -> tuple[float, tuple[str, ...]]:
    """Return a small score delta from explicit score evidence."""
    score = 0.0
    reasons: list[str] = []

    if mode == "walking" and directive.walking_pressure > 0:
        amount = directive.walking_pressure
        if harmonic_role in {"chord_tone", "diatonic_passing", "scale_color"}:
            score += .045 * amount
            reasons.append("scorebook walking evidence supports connective motion")
        elif harmonic_role == "root" and metric_role == "continuation":
            score -= .025 * amount
            reasons.append("scorebook walking evidence reduces middle-beat re-anchoring")
        elif harmonic_role in {"chromatic_approach", "anticipation"}:
            score += .010 * amount


    prior = directive.written_part_prior
    if prior is not None:
        if harmonic_role == "root":
            score += .04 * prior.root_preference
            reasons.append("written-part abstract prior supports root occupancy")
        elif harmonic_role in {"diatonic_passing", "scale_color"}:
            score += .05 * prior.scalar_preference
            reasons.append("written-part abstract prior supports scalar motion")
        elif harmonic_role in {"chromatic_approach", "neighbor"}:
            score += .05 * prior.chromatic_preference
            reasons.append("written-part abstract prior supports chromatic motion")

    if mode == "two_feel" and directive.two_feel_pressure > 0:
        amount = directive.two_feel_pressure
        if harmonic_role in {"root", "fifth"}:
            score += .055 * amount
            reasons.append("scorebook two-feel evidence reinforces root/fifth support")
        elif harmonic_role in {
            "chord_tone", "diatonic_passing", "neighbor", "scale_color"
        }:
            score -= .045 * amount
            reasons.append("scorebook two-feel evidence restrains color motion")

    return score, tuple(reasons)


def derive_bass_score_context(
    snapshot: ScoreContextSnapshot,
) -> BassScoreEvidenceDirective:
    """Translate resolved Shared Core score context into soft Bass pressure.

    Bass consumes Core's evidence-bounded runtime snapshot rather than
    re-resolving score position, navigation, or page evidence itself.
    """
    walking = 0.0
    two_feel = 0.0
    written = snapshot.written_part_role is not None
    reasons: list[str] = []

    feel_tokens = tuple(
        x for x in (
            snapshot.current_feel,
            snapshot.feel_change_here,
        )
        if x
    )
    for value in feel_tokens:
        token = value.lower()
        if "two feel" in token or "2 feel" in token or "back to 2" in token:
            two_feel = max(two_feel, snapshot.confidence)
            reasons.append(f"Core score context feel: {value}")
        if "in four" in token or "4 feel" in token or "walking" in token:
            walking = max(walking, snapshot.confidence)
            reasons.append(f"Core score context feel: {value}")

    for instrument, value in snapshot.player_instructions:
        if instrument != "bass":
            continue
        token = value.lower()
        if "walk" in token or "in four" in token:
            walking = max(walking, snapshot.confidence)
            reasons.append(f"Core bass instruction: {value}")
        if "two feel" in token or "2 feel" in token:
            two_feel = max(two_feel, snapshot.confidence)
            reasons.append(f"Core bass instruction: {value}")

    preferred = None
    if walking > two_feel + .10:
        preferred = "walking"
    elif two_feel > walking + .10:
        preferred = "two_feel"

    return BassScoreEvidenceDirective(
        preferred_mode=preferred,
        walking_pressure=walking,
        two_feel_pressure=two_feel,
        written_part_available=written,
        confidence=snapshot.confidence,
        provenance=snapshot.provenance,
        reasons=tuple(reasons),
    )
