"""Legacy compatibility alias for players.drums.comping_phrase."""
from importlib import import_module as _import_module
import sys as _sys

_impl = _import_module("players.drums.comping_phrase")
_sys.modules[__name__] = _impl
