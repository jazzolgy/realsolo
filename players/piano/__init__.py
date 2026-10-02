"""AI Pianist instrument layer.

Shared harmony, phrase, ensemble reasoning, sonority semantics, and generic
polyphonic evaluation come from Core. This package owns piano-specific
realization, comping, and interaction policy.
"""

from .ensemble_role import (
    PianoEnsembleMode,
    PianoEnsembleRoleContext,
    PianoHandFunction,
    PianoHandRolePlan,
    derive_piano_hand_role_plan,
)
from .rh_lh_interaction import (
    RHLHInteractionBias,
    RHLHRelation,
    evaluate_rh_lh_interaction,
)
from .lh_texture import (
    LHTextureBias,
    LHTextureClass,
    classify_lh_texture,
    evaluate_lh_texture_bias,
)
from .lh_voice_leading import (
    LHVoiceLeadingBias,
    evaluate_lh_voice_leading,
)
from .linear_practice_comparator import (
    AbstractWrittenLineObservation,
    ContourClass,
    IntervalMotionClass,
    LinearPracticeComparison,
    MotionSourceClass,
    TargetHorizonClass,
    compare_abstract_routes,
)
from .scorebook_evidence import (
    PianoScorebookEvidenceView,
    build_piano_scorebook_evidence_view,
)
from .shared_linear_adapter import realize_shared_linear_affordances
from .bebop_solo_runtime import (
    BebopSoloTickPlan,
    build_bebop_solo_tick,
    perform_bebop_solo_tick,
)
from .bebop_solo_candidates import generate_immediate_bebop_candidates
from .bebop_phrase_intent import (
    BebopDensityDirection,
    BebopEntryMode,
    BebopPhraseIntent,
    BebopTargetMode,
    derive_bebop_phrase_intent,
)
from .bebop_harmonic_turn import (
    BebopHarmonicPhase,
    BebopHarmonicTurnContext,
    derive_bebop_harmonic_turn_context,
)
from .bebop_harmonic_turn_comping import (
    BebopHarmonicTurnCompingBias,
    evaluate_bebop_harmonic_turn_comping_bias,
)
from .bebop_turn_taking import (
    BebopTurnTakingEvidence,
    BebopTurnTakingType,
    classify_bebop_turn_taking,
)
from .bebop_complementarity import (
    EnsembleBreathType,
    EnsembleComplementarityEvidence,
    SupportCarryMode,
    classify_ensemble_complementarity,
    support_carry_mode,
)
from .bebop_comping_breath import (
    BebopBreathCompingBias,
    evaluate_bebop_breath_comping_bias,
)
from .bebop_phrase_space import (
    BebopPhraseSpaceEvidence,
    PhraseSpaceType,
    classify_phrase_space,
)
from .solo import (
    PianoSoloContext,
    PianoSoloEvaluator,
    PianoSoloState,
    default_bebop_legend_blend,
    perform_one_piano_solo_event,
)
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
from .harmonic_creativity import (
    HarmonicCreativeFreedom,
    adapt_continuity_profile_for_harmony,
    adapt_creativity_context_for_harmony,
    assess_harmonic_creative_freedom,
)
from .harmonic_semantics import annotate_harmonic_semantics, harmonic_semantic_tags
from .creative_continuity import (
    CreativityContext,
    CreativeContinuityScore,
    DimensionContinuityProfile,
    evaluate_creative_continuity,
    profile_from_harmonic_context,
)
from .harmonic_continuity import (
    HarmonicContinuityFeatures,
    HarmonicContinuityMemory,
    HarmonicFingerprint,
    estimate_harmonic_continuity,
)
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
from .constraint_evaluator import ConstraintAwarePianoCompingEvaluator
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
    "PianoEnsembleMode",
    "PianoEnsembleRoleContext",
    "PianoHandFunction",
    "PianoHandRolePlan",
    "derive_piano_hand_role_plan",
    "RHLHInteractionBias",
    "RHLHRelation",
    "evaluate_rh_lh_interaction",
    "LHTextureBias",
    "LHTextureClass",
    "classify_lh_texture",
    "evaluate_lh_texture_bias",
    "LHVoiceLeadingBias",
    "evaluate_lh_voice_leading",
    "AbstractWrittenLineObservation",
    "ContourClass",
    "IntervalMotionClass",
    "LinearPracticeComparison",
    "MotionSourceClass",
    "TargetHorizonClass",
    "compare_abstract_routes",
    "PianoScorebookEvidenceView",
    "build_piano_scorebook_evidence_view",
    "realize_shared_linear_affordances",
    "BebopSoloTickPlan",
    "build_bebop_solo_tick",
    "perform_bebop_solo_tick",
    "generate_immediate_bebop_candidates",
    "BebopDensityDirection",
    "BebopEntryMode",
    "BebopPhraseIntent",
    "BebopTargetMode",
    "derive_bebop_phrase_intent",
    "BebopHarmonicPhase",
    "BebopHarmonicTurnContext",
    "derive_bebop_harmonic_turn_context",
    "BebopHarmonicTurnCompingBias",
    "evaluate_bebop_harmonic_turn_comping_bias",
    "BebopTurnTakingEvidence",
    "BebopTurnTakingType",
    "classify_bebop_turn_taking",
    "EnsembleBreathType",
    "EnsembleComplementarityEvidence",
    "SupportCarryMode",
    "classify_ensemble_complementarity",
    "support_carry_mode",
    "BebopBreathCompingBias",
    "evaluate_bebop_breath_comping_bias",
    "BebopPhraseSpaceEvidence",
    "PhraseSpaceType",
    "classify_phrase_space",
    "PianoSoloContext",
    "PianoSoloEvaluator",
    "PianoSoloState",
    "default_bebop_legend_blend",
    "perform_one_piano_solo_event",
    "PianoRealizationCandidate",
    "perform_one_piano_action",
    "CompingActionType",
    "InteractionRole",
    "PianoCompingCandidate",
    "PianoCompingContext",
    "PianoCompingEvaluator",
    "ConstraintAwarePianoCompingEvaluator",
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
    "HarmonicContinuityFeatures",
    "HarmonicContinuityMemory",
    "HarmonicFingerprint",
    "estimate_harmonic_continuity",
    "CreativityContext",
    "CreativeContinuityScore",
    "DimensionContinuityProfile",
    "evaluate_creative_continuity",
    "profile_from_harmonic_context",
    "HarmonicCreativeFreedom",
    "adapt_continuity_profile_for_harmony",
    "adapt_creativity_context_for_harmony",
    "assess_harmonic_creative_freedom",
    "annotate_harmonic_semantics",
    "harmonic_semantic_tags",
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
