"""Resumable autonomous research-listener state machine."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .research_listener import (
    ResearchListenerPolicy,
    ResearchSourceCandidate,
    ResearchSourceState,
    choose_next_research_source,
)


class ListenerRunState(str, Enum):
    IDLE="idle"
    SEARCHING="searching"
    READY="ready"
    PLAYING="playing"
    ANALYZING="analyzing"
    PAUSED="paused"
    BLOCKED="blocked"
    FAILED="failed"


@dataclass
class AutonomousResearchSession:
    """Provider-neutral queue controller for long-running listening.

    The controller is resumable and deterministic. Playback/capture are external
    side effects supplied by the browser/OS boundary.
    """

    policy: ResearchListenerPolicy = field(default_factory=ResearchListenerPolicy)
    run_state: ListenerRunState = ListenerRunState.IDLE
    queue: list[ResearchSourceCandidate] = field(default_factory=list)
    current: ResearchSourceCandidate | None = None
    completed_source_ids: set[str] = field(default_factory=set)
    failed_source_ids: set[str] = field(default_factory=set)
    blocked_source_ids: set[str] = field(default_factory=set)

    def replace_candidates(self, candidates: tuple[ResearchSourceCandidate,...]) -> None:
        self.queue=list(candidates)
        self.run_state=ListenerRunState.READY if self.queue else ListenerRunState.SEARCHING

    def choose_next(self) -> ResearchSourceCandidate | None:
        eligible=tuple(
            item for item in self.queue
            if item.source_id not in self.completed_source_ids
            and item.source_id not in self.failed_source_ids
            and item.source_id not in self.blocked_source_ids
        )
        self.current=choose_next_research_source(eligible,self.policy)
        self.run_state=ListenerRunState.READY if self.current else ListenerRunState.SEARCHING
        return self.current

    def mark_playing(self) -> None:
        if self.current is None:
            raise RuntimeError("no current source")
        self.run_state=ListenerRunState.PLAYING

    def mark_analyzing(self) -> None:
        if self.current is None:
            raise RuntimeError("no current source")
        self.run_state=ListenerRunState.ANALYZING

    def mark_complete(self) -> None:
        if self.current is None:
            raise RuntimeError("no current source")
        self.completed_source_ids.add(self.current.source_id)
        self.queue=[x for x in self.queue if x.source_id != self.current.source_id]
        self.current=None
        self.run_state=ListenerRunState.SEARCHING

    def pause(self) -> None:
        self.run_state=ListenerRunState.PAUSED

    def fail_current(self) -> None:
        if self.current is not None:
            self.failed_source_ids.add(self.current.source_id)
        self.current=None
        self.run_state=ListenerRunState.FAILED

    def block_current(self) -> None:
        if self.current is not None:
            self.blocked_source_ids.add(self.current.source_id)
        self.current=None
        self.run_state=ListenerRunState.BLOCKED

    def resume(self) -> None:
        self.run_state=ListenerRunState.READY if self.queue else ListenerRunState.SEARCHING
