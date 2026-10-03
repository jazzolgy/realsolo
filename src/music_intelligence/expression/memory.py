"""Shared memory for HOW a motif/phrase has recently been expressed.

This memory stores expressive summaries, not future notes.  It lets repeated
material vary dynamics/accent/body/foreground instead of replaying the same
absolute performance stamp.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from music_intelligence.learning.score_alignment import MusicalScoreCoordinate

from .representation import ExpressiveContext, ExpressiveIntent


@dataclass(frozen=True)
class MotifExpressionMemoryEntry:
    motif_id: str
    usage_count: int = 0
    last_intent: ExpressiveIntent | None = None
    last_position: MusicalScoreCoordinate | None = None

    def validate(self) -> None:
        if not self.motif_id:
            raise ValueError("motif_id is required")
        if self.usage_count < 0:
            raise ValueError("usage_count may not be negative")
        if self.last_intent is not None:
            self.last_intent.validate()
        if self.last_position is not None:
            self.last_position.validate()


@dataclass
class MotifExpressionMemory:
    entries: dict[str, MotifExpressionMemoryEntry] = field(default_factory=dict)

    def repetition_index(self, motif_id: str) -> int:
        entry=self.entries.get(motif_id)
        return 0 if entry is None else entry.usage_count

    def contextualize(
        self,
        motif_id: str,
        context: ExpressiveContext,
    ) -> ExpressiveContext:
        """Inject recent HOW-history without choosing a future event."""
        context.validate()
        entry=self.entries.get(motif_id)
        if entry is None:
            return context

        repetition=max(context.repetition_index,entry.usage_count)

        # If the previous realization was already strongly foreground/loud,
        # repeated material gets mild contrast pressure rather than automatic
        # crescendo.  This is a bounded immediate-context adjustment.
        target=context.target_foreground_weight
        climax=context.climax_pressure
        release=context.release_pressure
        if entry.last_intent is not None:
            if entry.last_intent.dynamic_level>=.72:
                target=max(0.0,target-.06)
                release=min(1.0,release+.08)
            elif entry.last_intent.dynamic_level<=.32:
                climax=min(1.0,climax+.05)

        return ExpressiveContext(
            position=context.position,
            phrase_maturity=context.phrase_maturity,
            tension=context.tension,
            ensemble_density=context.ensemble_density,
            current_foreground_weight=context.current_foreground_weight,
            target_foreground_weight=target,
            register_height=context.register_height,
            repetition_index=repetition,
            boundary_pressure=context.boundary_pressure,
            climax_pressure=climax,
            release_pressure=release,
            expressive_phase=context.expressive_phase,
        )

    def observe(
        self,
        motif_id: str,
        intent: ExpressiveIntent,
        *,
        position: MusicalScoreCoordinate | None = None,
    ) -> MotifExpressionMemoryEntry:
        """Record HOW only after an event/gesture has actually been committed."""
        if not motif_id:
            raise ValueError("motif_id is required")
        intent.validate()
        if position is not None:
            position.validate()
        prev=self.entries.get(motif_id)
        entry=MotifExpressionMemoryEntry(
            motif_id=motif_id,
            usage_count=1 if prev is None else prev.usage_count+1,
            last_intent=intent,
            last_position=position,
        )
        entry.validate()
        self.entries[motif_id]=entry
        return entry
