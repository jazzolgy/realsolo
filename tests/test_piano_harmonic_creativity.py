from dataclasses import replace

from music_intelligence.harmony.hypothesis_engine import ConfidenceVector, HarmonicHypothesis
from music_intelligence.harmony.jazz_harmony_core import HarmonicEvidence, HarmonicFrame, HarmonySource
from music_intelligence.harmony.orchestrator import HarmonicReasoningInput, reason_about_harmony
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from players.piano import (
    CreativityContext,
    DimensionContinuityProfile,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    adapt_continuity_profile_for_harmony,
    assess_harmonic_creative_freedom,
    build_contextual_comping_candidates,
)


def dominant_material():
    return ResolvedHarmonicMaterial(
        affordance_id="dominant.altered_color",
        root_pitch_class=7,
        role_pitch_classes={
            "root": (7,),
            "3rd": (11,),
            "b7": (5,),
            "b9": (8,),
            "#9": (10,),
            "b13": (3,),
        },
    )


def dominant_reasoning(ambiguous=False):
    hypotheses=(
        HarmonicHypothesis(
            "g7", "G7 dominant", function="dominant",
            interpretation_family="functional",
            confidence=ConfidenceVector(observed=.92,inferred=.92),
        ),
    )
    if ambiguous:
        hypotheses += (
            HarmonicHypothesis(
                "modal", "G mixolydian/modal", function="modal_tonic",
                interpretation_family="modal",
                confidence=ConfidenceVector(observed=.9,modal_context=.9),
            ),
        )
    return reason_about_harmony(HarmonicReasoningInput(
        frame=HarmonicFrame(
            expected=HarmonicEvidence(
                HarmonySource.EXPECTED,symbol="G7",root_pc=7,function="dominant"
            ),
            inferred=HarmonicEvidence(
                HarmonySource.INFERRED,symbol="G7alt",root_pc=7,function="dominant"
            ),
            next_expected=HarmonicEvidence(
                HarmonySource.EXPECTED,symbol="Cmaj7",root_pc=0,function="tonic"
            ),
            tension=.75,
        ),
        hypotheses=hypotheses,
    ))


def test_planner_candidates_expose_core_facing_harmonic_semantics():
    slate=build_contextual_comping_candidates(
        PianoVoicingRequest(dominant_material()),
        PianoCompingContext(section_energy=.7),
    )
    shell=next(c for c in slate.candidates if c.realization is not None and "shell" in c.tags)
    assert "guide_tone" in shell.realization.event.tags
    assert "harmonic_identity" in shell.realization.event.tags

    rootless=next(c for c in slate.candidates if c.realization is not None and "rootless" in c.tags)
    assert "extension" in rootless.realization.event.tags
    assert "color_tone" in rootless.realization.event.tags


def test_altered_rootless_candidate_exposes_altered_semantics():
    slate=build_contextual_comping_candidates(
        PianoVoicingRequest(dominant_material()),
        PianoCompingContext(section_energy=.7),
    )
    altered=next(
        c for c in slate.candidates
        if c.realization is not None
        and "rootless" in c.tags
        and "altered" in c.realization.event.tags
    )
    assert "tension" in altered.realization.event.tags
    assert "high_tension" in altered.realization.event.tags


def test_harmonic_ambiguity_loosens_reversible_expression_dimensions():
    base=DimensionContinuityProfile(
        role=.8,family=.8,rhythm=.8,register=.6,dynamic=.6,touch=.6
    )
    clear=adapt_continuity_profile_for_harmony(base,dominant_reasoning(False))
    ambiguous=adapt_continuity_profile_for_harmony(base,dominant_reasoning(True))
    assert ambiguous.register <= clear.register
    assert ambiguous.dynamic <= clear.dynamic
    assert ambiguous.touch <= clear.touch


def test_uncertainty_without_plural_options_does_not_grant_large_family_freedom():
    ambiguous=dominant_reasoning(True)
    no_options=replace(
        ambiguous,
        action_options=(),
        uncertainty=.95,
        needs_more_evidence=True,
    )
    freedom=assess_harmonic_creative_freedom(no_options)
    assert freedom.reversible_freedom == .95
    assert freedom.harmonic_family_freedom == 0.0


def test_plural_credible_harmonic_options_enable_some_family_freedom():
    harmony=dominant_reasoning(False)
    freedom=assess_harmonic_creative_freedom(harmony)
    assert freedom.option_diversity > 0
    assert freedom.harmonic_family_freedom > 0


def test_piano_evaluator_consumes_shared_v142_harmonic_guidance():
    harmony=dominant_reasoning(False)
    ctx=PianoCompingContext(section_energy=.6)
    slate=build_contextual_comping_candidates(
        PianoVoicingRequest(dominant_material()),
        ctx,
    )
    shell=next(c for c in slate.candidates if c.realization is not None and "shell" in c.tags)
    score=PianoCompingEvaluator().evaluate(
        shell,
        ctx,
        MusicalContextVector(chord_symbol="G7",ensemble_activity=.4),
        PianoCompingState(),
        harmonic_reasoning=harmony,
    )
    assert score.components.get("shared_harmonic_guidance_total",0) > 0


def test_harmonic_creativity_still_contains_no_future_solution():
    harmony=dominant_reasoning(True)
    freedom=assess_harmonic_creative_freedom(harmony)
    assert not hasattr(freedom,"future_voicings")
    assert not hasattr(freedom,"future_harmony")
    assert not hasattr(freedom,"planned_sequence")