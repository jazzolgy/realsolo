"""Legacy compatibility alias for players.bass.immediate_realizer."""
from importlib import import_module as _import_module
import sys as _sys

_impl = _import_module("players.bass.immediate_realizer")
_sys.modules[__name__] = _impl
