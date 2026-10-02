"""Legacy compatibility alias for players.drums.online_drummer."""
from importlib import import_module as _import_module
import sys as _sys

_impl = _import_module("players.drums.online_drummer")
_sys.modules[__name__] = _impl
