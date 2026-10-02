"""Identity-level motif transformations.

Transforms relative motif identity only; no exact future notes are produced.
"""
from __future__ import annotations
from dataclasses import replace

from .representation import MotifIdentity
from ..solo_grammar import SoloDevelopmentOperation


def transform_motif(
    identity: MotifIdentity,
    operation: SoloDevelopmentOperation,
) -> MotifIdentity:
    identity.validate()
    intervals = identity.interval_schema
    rhythms = identity.rhythm_schema

    if operation is SoloDevelopmentOperation.INVERT:
        intervals = tuple(-x for x in intervals)
    elif operation is SoloDevelopmentOperation.FRAGMENT:
        intervals = intervals[: max(1, len(intervals)//2)] if intervals else ()
        rhythms = rhythms[: max(1, len(rhythms)//2)] if rhythms else ()
    elif operation is SoloDevelopmentOperation.AUGMENT:
        rhythms = tuple(x * 2.0 for x in rhythms)
    elif operation is SoloDevelopmentOperation.DIMINISH:
        rhythms = tuple(max(.125, x * .5) for x in rhythms)
    elif operation is SoloDevelopmentOperation.SEQUENCE:
        # Preserve identity; sequence position is determined online by harmony.
        pass
    elif operation is SoloDevelopmentOperation.CONTRACT:
        intervals = intervals[:-1] if len(intervals) > 1 else intervals
        rhythms = rhythms[:-1] if len(rhythms) > 2 else rhythms

    out = replace(
        identity,
        motif_id=f"{identity.motif_id}:{operation.value}",
        interval_schema=intervals,
        rhythm_schema=rhythms,
        provenance=identity.provenance + (f"transform:{operation.value}",),
    )
    out.validate()
    return out
