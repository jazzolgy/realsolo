"""Shared policy for how strongly vocabulary may be reused by use type.

Signature status belongs to Legend evidence. This module owns generic reuse
pressure and transformation preference.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.legends.interfaces import (
    SignatureStatus,
    VocabularyMemoryItem,
    VocabularyQuery,
    VocabularyUseType,
)


@dataclass(frozen=True)
class VocabularyUseScore:
    signature_bias: float = 0.0
    use_bias: float = 0.0
    scarcity_penalty: float = 0.0

    @property
    def total(self) -> float:
        return self.signature_bias + self.use_bias - self.scarcity_penalty


_USE_BASE_BIAS: dict[VocabularyUseType, float] = {
    VocabularyUseType.LITERAL_QUOTE: -0.08,
    VocabularyUseType.TRANSPOSED_LICK: -0.04,
    VocabularyUseType.ADAPTED_LICK: 0.00,
    VocabularyUseType.FRAGMENT_RECALL: 0.035,
    VocabularyUseType.ABSTRACTED_PATTERN: 0.050,
    VocabularyUseType.HYBRID_COMPOSITION: 0.065,
}

# Recent-use pressure grows fastest for recognizable reuse.
_RECENT_USE_MULTIPLIER: dict[VocabularyUseType, float] = {
    VocabularyUseType.LITERAL_QUOTE: 2.25,
    VocabularyUseType.TRANSPOSED_LICK: 1.75,
    VocabularyUseType.ADAPTED_LICK: 1.25,
    VocabularyUseType.FRAGMENT_RECALL: 0.90,
    VocabularyUseType.ABSTRACTED_PATTERN: 0.65,
    VocabularyUseType.HYBRID_COMPOSITION: 0.50,
}

DIRECT_LITERAL_SHARE = 0.30

_SIGNATURE_BIAS: dict[SignatureStatus, float] = {
    SignatureStatus.NONE: 0.0,
    SignatureStatus.RECURRING: 0.015,
    SignatureStatus.SIGNATURE_CANDIDATE: 0.030,
    SignatureStatus.SIGNATURE_CONFIRMED: 0.045,
}


def _effective_use(
    item: VocabularyMemoryItem,
    request: VocabularyQuery,
) -> VocabularyUseType:
    if request.preferred_use is not None:
        return request.preferred_use

    # If the caller does not choose a use, prefer the least literal eligible use.
    preference = (
        VocabularyUseType.HYBRID_COMPOSITION,
        VocabularyUseType.ABSTRACTED_PATTERN,
        VocabularyUseType.FRAGMENT_RECALL,
        VocabularyUseType.ADAPTED_LICK,
        VocabularyUseType.TRANSPOSED_LICK,
        VocabularyUseType.LITERAL_QUOTE,
    )
    allowed = item.candidate_uses.intersection(request.allowed_uses)
    for use in preference:
        if use in allowed:
            return use
    return VocabularyUseType.HYBRID_COMPOSITION


def vocabulary_use_score(
    item: VocabularyMemoryItem,
    request: VocabularyQuery,
) -> VocabularyUseScore:
    use = _effective_use(item, request)
    if use not in item.candidate_uses or use not in request.allowed_uses:
        return VocabularyUseScore(scarcity_penalty=1.0)

    signature_bias = _SIGNATURE_BIAS[item.signature_status]
    use_bias = _USE_BASE_BIAS[use]

    recent_pressure = min(
        0.45,
        0.04 * item.recent_usage_count * _RECENT_USE_MULTIPLIER[use],
    )

    # Confirmed signature material should be recognizable but not over-quoted.
    # Transformations can use its identity more freely than literal quotation.
    if item.signature_status is SignatureStatus.SIGNATURE_CONFIRMED:
        if use is VocabularyUseType.LITERAL_QUOTE:
            recent_pressure += 0.12
        elif use is VocabularyUseType.TRANSPOSED_LICK:
            recent_pressure += 0.07
        elif use is VocabularyUseType.ADAPTED_LICK:
            recent_pressure += 0.025
        elif use in {
            VocabularyUseType.FRAGMENT_RECALL,
            VocabularyUseType.ABSTRACTED_PATTERN,
            VocabularyUseType.HYBRID_COMPOSITION,
        }:
            use_bias += 0.020

    return VocabularyUseScore(
        signature_bias=signature_bias,
        use_bias=use_bias,
        scarcity_penalty=min(0.60, recent_pressure),
    )



def choose_runtime_vocabulary_use(
    item: VocabularyMemoryItem,
    request: VocabularyQuery,
    *,
    opportunity_index: int,
) -> VocabularyUseType:
    """Choose direct vs transformed reuse for one runtime opportunity.

    Project listening policy:
    - when verified literal material is available and literal use is allowed,
      about 30 percent of opportunities may use it directly;
    - remaining opportunities prefer transformed reuse;
    - no literal representation means automatic transformed fallback.

    The 3-of-10 slot schedule is deterministic so research rehearsals are
    reproducible. It is a usage target, not a requirement that every phrase
    contain exactly 30 percent literal material.
    """
    item.validate()
    if opportunity_index < 0:
        raise ValueError("opportunity_index may not be negative")

    allowed=item.candidate_uses.intersection(request.allowed_uses)
    if request.preferred_use is not None:
        if request.preferred_use not in allowed:
            raise ValueError("preferred_use is not allowed for this vocabulary item")
        return request.preferred_use

    direct_slot=(opportunity_index % 10) < 3
    if (
        direct_slot
        and bool(item.literal_representation)
        and VocabularyUseType.LITERAL_QUOTE in allowed
    ):
        return VocabularyUseType.LITERAL_QUOTE

    transformed_preference=(
        VocabularyUseType.HYBRID_COMPOSITION,
        VocabularyUseType.ABSTRACTED_PATTERN,
        VocabularyUseType.FRAGMENT_RECALL,
        VocabularyUseType.ADAPTED_LICK,
        VocabularyUseType.TRANSPOSED_LICK,
    )
    for use in transformed_preference:
        if use in allowed:
            return use

    if bool(item.literal_representation) and VocabularyUseType.LITERAL_QUOTE in allowed:
        return VocabularyUseType.LITERAL_QUOTE

    raise ValueError(f"no eligible runtime vocabulary use for {item.vocabulary_id}")
