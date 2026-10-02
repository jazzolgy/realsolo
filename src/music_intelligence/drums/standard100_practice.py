"""Legacy compatibility alias for players.drums.standard100_practice."""
from importlib import import_module as _import_module
import sys as _sys

_impl = _import_module("players.drums.standard100_practice")
_sys.modules[__name__] = _impl
