"""Legacy compatibility alias for players.drums.ride_continuity."""
from importlib import import_module as _import_module
import sys as _sys

_impl = _import_module("players.drums.ride_continuity")
_sys.modules[__name__] = _impl
