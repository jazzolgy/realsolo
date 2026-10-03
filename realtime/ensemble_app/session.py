from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .chart import SongChart
from .chart_transport import ChartPosition, ChartTransport


class UserRole(str, Enum):
    SOLOIST = "soloist"
    COMPER = "comper"


class AIRole(str, Enum):
    ACCOMPANIMENT = "accompaniment"
    SOLOIST = "soloist"


@dataclass(frozen=True, slots=True)
class SessionConfig:
    chart: SongChart
    user_role: UserRole
    ai_role: AIRole

    @classmethod
    def for_user_role(cls, chart: SongChart, user_role: UserRole) -> "SessionConfig":
        ai_role = AIRole.ACCOMPANIMENT if user_role == UserRole.SOLOIST else AIRole.SOLOIST
        return cls(chart=chart, user_role=user_role, ai_role=ai_role)


class PracticeSession:
    """Stage-1 chart/session shell independent of microphone perception."""

    def __init__(self, config: SessionConfig) -> None:
        self.config = config
        self.transport = ChartTransport(config.chart)

    def start(self, now: float) -> None:
        self.transport.start(now)

    def position(self, now: float) -> ChartPosition:
        return self.transport.position(now)
