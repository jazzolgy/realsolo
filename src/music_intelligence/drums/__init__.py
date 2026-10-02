"""Compatibility shim for legacy Drum imports.

Canonical implementation lives in players.drums.
"""
from players import drums as _impl
from players.drums import *  # noqa: F401,F403

__all__ = tuple(_impl.__all__)
