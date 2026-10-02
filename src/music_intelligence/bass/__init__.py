"""Compatibility shim for legacy Bass imports.

Canonical implementation lives in players.bass.
"""
from players import bass as _impl
from players.bass import *  # noqa: F401,F403

__all__ = tuple(_impl.__all__)
