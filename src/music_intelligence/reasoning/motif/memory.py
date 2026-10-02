"""Shared motif memory: active → thematic → dormant → reactivated."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

from .representation import MotifIdentity


class MotifMemoryState(str, Enum):
    ACTIVE = "active"
    THEMATIC = "thematic"
    DORMANT = "dormant"


@dataclass(frozen=True)
class MotifMemoryEntry:
    identity: MotifIdentity
    state: MotifMemoryState = MotifMemoryState.ACTIVE
    usage_count: int = 0
    successful_developments: int = 0
    last_seen_tick: int = 0
    recall_strength: float = .5

    def validate(self) -> None:
        self.identity.validate()
        if self.usage_count < 0 or self.successful_developments < 0 or self.last_seen_tick < 0:
            raise ValueError("motif memory counts may not be negative")
        if not 0.0 <= self.recall_strength <= 1.0:
            raise ValueError("recall_strength must be within 0..1")


@dataclass
class MotifMemory:
    entries: dict[str, MotifMemoryEntry] = field(default_factory=dict)
    tick: int = 0

    def observe(
        self,
        identity: MotifIdentity,
        *,
        development_success: float = .5,
    ) -> MotifMemoryEntry:
        identity.validate()
        if not 0.0 <= development_success <= 1.0:
            raise ValueError("development_success must be within 0..1")
        self.tick += 1
        prev = self.entries.get(identity.motif_id)
        uses = 1 if prev is None else prev.usage_count + 1
        successes = (0 if prev is None else prev.successful_developments) + (1 if development_success >= .65 else 0)
        state = MotifMemoryState.THEMATIC if uses >= 2 and successes >= 1 else MotifMemoryState.ACTIVE
        entry = MotifMemoryEntry(
            identity=identity,
            state=state,
            usage_count=uses,
            successful_developments=successes,
            last_seen_tick=self.tick,
            recall_strength=min(1.0, .42 + .12 * uses + .10 * successes),
        )
        entry.validate()
        self.entries[identity.motif_id] = entry
        return entry

    def advance(self, dormant_after_ticks: int = 8) -> None:
        if dormant_after_ticks <= 0:
            raise ValueError("dormant_after_ticks must be positive")
        self.tick += 1
        for key, entry in tuple(self.entries.items()):
            if self.tick - entry.last_seen_tick >= dormant_after_ticks:
                self.entries[key] = MotifMemoryEntry(
                    identity=entry.identity,
                    state=MotifMemoryState.DORMANT,
                    usage_count=entry.usage_count,
                    successful_developments=entry.successful_developments,
                    last_seen_tick=entry.last_seen_tick,
                    recall_strength=max(.1, entry.recall_strength * .86),
                )

    def active(self) -> tuple[MotifMemoryEntry, ...]:
        return tuple(
            x for x in self.entries.values()
            if x.state in {MotifMemoryState.ACTIVE, MotifMemoryState.THEMATIC}
        )

    def recall(self, motif_id: str) -> MotifMemoryEntry | None:
        entry = self.entries.get(motif_id)
        if entry is None:
            return None
        if entry.state is MotifMemoryState.DORMANT:
            reactivated = MotifMemoryEntry(
                identity=entry.identity,
                state=MotifMemoryState.ACTIVE,
                usage_count=entry.usage_count,
                successful_developments=entry.successful_developments,
                last_seen_tick=self.tick,
                recall_strength=min(1.0, entry.recall_strength + .12),
            )
            self.entries[motif_id] = reactivated
            return reactivated
        return entry
