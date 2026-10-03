"""Reactive live ensemble runtime.

The package root stays lightweight. Player-specific native deciders are loaded
lazily so Shared-Core adapters can be imported without forcing every Player API
at module-import time.
"""

from .engine import EnsembleEngine
from .models import EnsembleState, MidiObservation, MusicalAction
from .runtime_loop import (
    EnsemblePlayerProvider,
    EnsembleRuntimeLoop,
    PlayerRuntimeDecision,
    RuntimeTickResult,
    committed_intent,
)
from .trio_adapters import (
    BassRuntimeAdapter,
    DrumsRuntimeAdapter,
    NativeImmediateResult,
    PianoRuntimeAdapter,
    TrioAdapterStatus,
    trio_adapter_status,
)

__all__ = [
    "EnsembleEngine",
    "EnsembleState",
    "MidiObservation",
    "MusicalAction",
    "EnsemblePlayerProvider",
    "EnsembleRuntimeLoop",
    "PlayerRuntimeDecision",
    "RuntimeTickResult",
    "committed_intent",
    "BassRuntimeAdapter",
    "DrumsRuntimeAdapter",
    "NativeImmediateResult",
    "PianoRuntimeAdapter",
    "TrioAdapterStatus",
    "trio_adapter_status",
    "BassNativeDecider",
    "DrumsNativeDecider",
    "PianoNativeDecider",
    "build_native_trio_runtime",
]


def __getattr__(name: str):
    if name in {
        "BassNativeDecider",
        "DrumsNativeDecider",
        "PianoNativeDecider",
        "build_native_trio_runtime",
    }:
        from . import native_deciders
        return getattr(native_deciders,name)
    raise AttributeError(name)
