"""Compatibility adapter from the new HOW intent to legacy solo-expression API."""
from __future__ import annotations

from music_intelligence.reasoning.solo_expression import SoloExpressionIntent

from .representation import ExpressiveIntent


def to_solo_expression_intent(intent: ExpressiveIntent) -> SoloExpressionIntent:
    intent.validate()
    # note_body maps to sounding/sustain tendency, while accent remains separate.
    sustain=max(.35,min(1.5,.55+1.0*intent.note_body))
    out=SoloExpressionIntent(
        dynamic_energy=intent.dynamic_level,
        accent=intent.accent_strength,
        sustain_ratio=sustain,
        timing_offset_beats=intent.timing_emphasis_beats,
        articulation_tags=intent.articulation_tags,
        confidence=intent.confidence,
        provenance=intent.provenance+("shared_expression_adapter",),
    )
    out.validate()
    return out
