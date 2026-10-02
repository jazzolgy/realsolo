"""Legacy compatibility alias for players.bass.render_projection."""
from importlib import import_module as _import_module
import sys as _sys

_impl = _import_module("players.bass.render_projection")
_sys.modules[__name__] = _impl
