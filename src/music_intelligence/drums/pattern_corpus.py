"""Legacy compatibility alias for players.drums.pattern_corpus."""
from importlib import import_module as _import_module
import sys as _sys

_impl = _import_module("players.drums.pattern_corpus")
_sys.modules[__name__] = _impl
