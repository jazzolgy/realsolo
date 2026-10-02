"""Public Bass player namespace.

Safe-migration facade: instrument policy is still implemented in
music_intelligence.bass so existing imports and realtime integration remain
stable. Do not add a second Bass policy here; migrate implementation only in a
separately tested change.
"""

from music_intelligence import bass as _impl
from music_intelligence.bass import *  # noqa: F401,F403

__all__ = tuple(_impl.__all__)
