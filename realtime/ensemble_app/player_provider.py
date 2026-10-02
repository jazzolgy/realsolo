from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .player_contract import RenderGesture


class ProviderState(str, Enum):
    FALLBACK = "fallback"
    PLAYER_BRANCH = "player_branch"
    CORE_PLAYER = "core_player"


class ImmediatePlayerProvider(Protocol):
    """App-facing provider contract.

    Implementations may live in player branches. They return only the currently
    committed gesture; candidate sets and musical policy remain outside the app.
    """

    role: str

    def decide_immediate(self, context: dict) -> RenderGesture | None: ...


@dataclass(frozen=True, slots=True)
class PlayerProviderStatus:
    role: str
    state: ProviderState
    source: str
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "state": self.state.value,
            "source": self.source,
            "detail": self.detail,
        }


def current_stage1_provider_status() -> tuple[PlayerProviderStatus, ...]:
    """Truthful integration status for the current realtime branch."""

    return (
        PlayerProviderStatus(
            "piano",
            ProviderState.PLAYER_BRANCH,
            "player/piano",
            "player implementation exists on its branch; awaiting integration into shared runtime",
        ),
        PlayerProviderStatus(
            "bass",
            ProviderState.PLAYER_BRANCH,
            "player/bass",
            "workstream exists; realtime still uses temporary fallback until committed gestures are exposed",
        ),
        PlayerProviderStatus(
            "drums",
            ProviderState.PLAYER_BRANCH,
            "player/drums",
            "workstream exists; realtime still uses temporary fallback until committed gestures are exposed",
        ),
        PlayerProviderStatus(
            "solo",
            ProviderState.CORE_PLAYER,
            "stage1 immediate Core bridge",
            "temporary chart-aware one-event solo adapter",
        ),
    )
