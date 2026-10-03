"""Durable local checkpoint for the autonomous research listener."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Iterable

from .autonomous_research_session import AutonomousResearchSession, ListenerRunState


def default_research_state_root() -> Path:
    return Path.home()/".local"/"share"/"realsolo"/"research"


@dataclass
class ResearchCheckpoint:
    completed_source_ids: list[str] = field(default_factory=list)
    failed_source_ids: list[str] = field(default_factory=list)
    blocked_source_ids: list[str] = field(default_factory=list)
    last_source_id: str | None = None
    last_query: str = ""
    last_artist: str = ""
    run_state: str = ListenerRunState.IDLE.value

    @classmethod
    def load(cls,path: Path) -> "ResearchCheckpoint":
        if not path.exists():
            return cls()
        raw=json.loads(path.read_text(encoding="utf-8"))
        return cls(
            completed_source_ids=list(raw.get("completed_source_ids",[])),
            failed_source_ids=list(raw.get("failed_source_ids",[])),
            blocked_source_ids=list(raw.get("blocked_source_ids",[])),
            last_source_id=raw.get("last_source_id"),
            last_query=str(raw.get("last_query","")),
            last_artist=str(raw.get("last_artist","")),
            run_state=str(raw.get("run_state",ListenerRunState.IDLE.value)),
        )

    def save(self,path: Path) -> None:
        path.parent.mkdir(parents=True,exist_ok=True)
        tmp=path.with_suffix(path.suffix+".tmp")
        tmp.write_text(json.dumps(asdict(self),ensure_ascii=False,indent=2),encoding="utf-8")
        tmp.replace(path)

    def restore_session(self,session: AutonomousResearchSession) -> None:
        session.completed_source_ids=set(self.completed_source_ids)
        session.failed_source_ids=set(self.failed_source_ids)
        session.blocked_source_ids=set(self.blocked_source_ids)
        try:
            session.run_state=ListenerRunState(self.run_state)
        except ValueError:
            session.run_state=ListenerRunState.IDLE

    @classmethod
    def from_session(
        cls,
        session: AutonomousResearchSession,
        *,
        last_query: str = "",
        last_artist: str = "",
    ) -> "ResearchCheckpoint":
        return cls(
            completed_source_ids=sorted(session.completed_source_ids),
            failed_source_ids=sorted(session.failed_source_ids),
            blocked_source_ids=sorted(session.blocked_source_ids),
            last_source_id=session.current.source_id if session.current else None,
            last_query=last_query,
            last_artist=last_artist,
            run_state=session.run_state.value,
        )
