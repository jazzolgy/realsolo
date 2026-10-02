"""Legacy compatibility alias for players.bass.practice_curriculum."""
from importlib import import_module as _import_module
import sys as _sys

_impl = _import_module("players.bass.practice_curriculum")
_sys.modules[__name__] = _impl
