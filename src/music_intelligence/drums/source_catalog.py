"""Legacy compatibility alias for players.drums.source_catalog."""
from importlib import import_module as _import_module
import sys as _sys

_impl = _import_module("players.drums.source_catalog")
_sys.modules[__name__] = _impl
