"""AI Pianist instrument layer.

Shared harmony, phrase, ensemble reasoning, sonority semantics, and generic
polyphonic evaluation come from Core. This package owns piano-specific
realization, comping, and interaction policy.
"""

from .policy import (
    PianoActionScore,
    PianoPerformanceState,
    PianoPolicyEvaluator,
    PianoRealizationCandidate,
    perform_one_piano_action,
)
from .interaction import EnergyDirection, PhraseSpaceWindow, PianoDensity, PianoInteractionState
from .voicing import (
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    generate_extended_voicing_families,
    generate_inverted_quartal_voicings,
    generate_minimal_voicing_families,
    generate_mixed_voicings,
    generate_octave_voicings,
    generate_quartal_voicings,
    generate_rootless_voicings,
    generate_shell_voicings,
    generate_tertian_voicings,
)
from .planner import PianoCompingCandidateSet, build_contextual_comping_candidates
from .comping import (
    CompingActionType,
    InteractionRole,
    PianoCompingCandidate,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingScore,
    PianoCompingState,
    perform_one_comping_action,
)

__all__ = [
    "PianoActionScore",
    "PianoPerformanceState",
    "PianoPolicyEvaluator",
    "PianoRealizationCandidate",
    "perform_one_piano_action",
    "CompingActionType",
    "InteractionRole",
    "PianoCompingCandidate",
    "PianoCompingContext",
    "PianoCompingEvaluator",
    "PianoCompingScore",
    "PianoCompingState",
    "perform_one_comping_action",
    "EnergyDirection",
    "PhraseSpaceWindow",
    "PianoDensity",
    "PianoInteractionState",
    "PianoVoicingRequest",
    "ResolvedHarmonicMaterial",
    "generate_extended_voicing_families",
    "generate_inverted_quartal_voicings",
    "generate_minimal_voicing_families",
    "generate_mixed_voicings",
    "generate_octave_voicings",
    "generate_quartal_voicings",
    "generate_rootless_voicings",
    "generate_shell_voicings",
    "generate_tertian_voicings",
    "PianoCompingCandidateSet",
    "build_contextual_comping_candidates",
]
