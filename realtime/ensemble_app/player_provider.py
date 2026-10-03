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
            ProviderState.CORE_PLAYER,
            "player/piano via native trio runtime",
            "Stage 1 consumes committed piano comping actions from the executable player runtime",
        ),
        PlayerProviderStatus(
            "bass",
            ProviderState.CORE_PLAYER,
            "player/bass via native trio runtime",
            "Stage 1 consumes committed bass actions; realtime fallback removed from accompaniment path",
        ),
        PlayerProviderStatus(
            "drums",
            ProviderState.CORE_PLAYER,
            "player/drums via native trio runtime",
            "Stage 1 consumes committed drum gestures; realtime fallback removed from accompaniment path",
        ),
        PlayerProviderStatus(
            "solo",
            ProviderState.CORE_PLAYER,
            "stage1 immediate Core bridge",
            "temporary chart-aware one-event solo adapter",
        ),
    )
