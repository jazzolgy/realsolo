"""Legacy compatibility alias for players.drums.bebop_profile."""
from importlib import import_module as _import_module
import sys as _sys

_impl = _import_module("players.drums.bebop_profile")
_sys.modules[__name__] = _impl
