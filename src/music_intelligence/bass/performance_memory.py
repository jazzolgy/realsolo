"""Legacy compatibility alias for players.bass.performance_memory."""
from importlib import import_module as _import_module
import sys as _sys

_impl = _import_module("players.bass.performance_memory")
_sys.modules[__name__] = _impl
