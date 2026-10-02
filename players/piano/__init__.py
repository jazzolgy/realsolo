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
from .planner import (
    PianoCompingCandidateSet,
    build_contextual_comping_candidates,
    build_immediate_performance_candidates,
    expand_candidate_set_rhythmically,
    expand_candidate_set_expressively,
)
from .narrative import NarrativeBiasScore, evaluate_narrative_bias
from .variation import GestureSignature, VariationContext, VariationScore, evaluate_variation
from .role_occupancy import (
    CompingPriority,
    CompingRoleOccupancy,
    RoleOccupancyBias,
    evaluate_role_occupancy_bias,
)
from .interaction_episode import (
    EpisodeBias,
    InteractionEpisode,
    InteractionEpisodeType,
    evaluate_episode_bias,
    infer_interaction_episode,
)
from .ensemble_response import (
    EnsembleActor,
    EnsembleResponseBias,
    EnsembleResponseObservation,
    EnsembleSnapshot,
    GestureResponseRecord,
    ResponseType,
    evaluate_response_bias,
    infer_coarse_responses,
)
from .expression import (
    DynamicLevel,
    PianoExpressionIntent,
    RegisterDirection,
    TouchType,
    apply_expression_intent,
    expand_expression_variants,
    expression_intents_for_candidate,
)
from .rhythm import (
    PianoRhythmicIntent,
    RhythmicPlacement,
    apply_rhythmic_intent,
    expand_rhythmic_variants,
    rhythmic_intents_for_candidate,
)
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
    "build_immediate_performance_candidates",
    "expand_candidate_set_rhythmically",
    "NarrativeBiasScore",
    "evaluate_narrative_bias",
    "GestureSignature",
    "VariationContext",
    "VariationScore",
    "evaluate_variation",
    "EnsembleActor",
    "EnsembleResponseBias",
    "EnsembleResponseObservation",
    "EnsembleSnapshot",
    "GestureResponseRecord",
    "ResponseType",
    "evaluate_response_bias",
    "infer_coarse_responses",
    "EpisodeBias",
    "InteractionEpisode",
    "InteractionEpisodeType",
    "evaluate_episode_bias",
    "infer_interaction_episode",
    "CompingPriority",
    "CompingRoleOccupancy",
    "RoleOccupancyBias",
    "evaluate_role_occupancy_bias",
    "PianoRhythmicIntent",
    "RhythmicPlacement",
    "apply_rhythmic_intent",
    "expand_rhythmic_variants",
    "rhythmic_intents_for_candidate",
    "DynamicLevel",
    "PianoExpressionIntent",
    "RegisterDirection",
    "TouchType",
    "apply_expression_intent",
    "expand_expression_variants",
    "expression_intents_for_candidate",
    "expand_candidate_set_expressively",
]
