"""Legacy compatibility alias for players.drums.practice_standard100."""
from importlib import import_module as _import_module
import sys as _sys

_impl = _import_module("players.drums.practice_standard100")
_sys.modules[__name__] = _impl
