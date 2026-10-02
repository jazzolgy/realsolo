"""Legacy compatibility alias for players.bass.sequential_runner."""
from importlib import import_module as _import_module
import sys as _sys

_impl = _import_module("players.bass.sequential_runner")
_sys.modules[__name__] = _impl
