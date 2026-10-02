from music_intelligence.harmony.contextual_tension import MusicalLayer, TensionContext
from music_intelligence.harmony.harmonic_time import CadenceStrength, TonicizationEvidence
from music_intelligence.harmony.hypothesis_engine import ConfidenceVector, HarmonicHypothesis
from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonicIntent,
    HarmonySource,
)
from music_intelligence.harmony.modal_nonfunctional import ModalState, VerticalTopology
from music_intelligence.harmony.orchestrator import HarmonicReasoningInput, reason_about_harmony
from music_intelligence.harmony.reharmonization import make_substitute_dominant_proposal
from music_intelligence.harmony.voice_leading import (
    TargetRole,
    VoiceLeadingContext,
    VoiceRole,
    VoiceState,
    make_resolution_debt,
)


def dominant_frame():
    return HarmonicFrame(
        expected=HarmonicEvidence(
            HarmonySource.EXPECTED, symbol="G7", root_pc=7, function="dominant"
        ),
        observed=HarmonicEvidence(
            HarmonySource.OBSERVED,
            symbol="G7alt",
            root_pc=7,
            pitch_classes=frozenset({7, 10, 3, 6}),
            confidence=.85,
        ),
        inferred=HarmonicEvidence(
            HarmonySource.INFERRED, symbol="G7alt", root_pc=7, function="dominant"
        ),
        next_expected=HarmonicEvidence(
            HarmonySource.EXPECTED, symbol="Cmaj7", root_pc=0, function="tonic"
        ),
        tension=.75,
    )


def test_orchestrator_composes_existing_harmony_layers():
    result = reason_about_harmony(HarmonicReasoningInput(
        frame=dominant_frame(),
        hypotheses=(
            HarmonicHypothesis(
                "g7alt", "G7 altered dominant", root_pc=7, function="dominant",
                interpretation_family="functional",
                confidence=ConfidenceVector(expected=.9, observed=.85, inferred=.9),
            ),
        ),
        modal_state=ModalState(
            tonic_pc=7, mode_name="G Mixolydian", current_bass_pc=7,
            vertical_topology=VerticalTopology.TERTIAN, functional_pull=.8,
        ),
        tonicization_evidence=TonicizationEvidence(
            tonic_pc=0, dominant_root_pc=7, resolves_to_target=True,
            target_duration_beats=4, target_repetitions=1,
            cadence_strength=CadenceStrength.MODERATE,
        ),
        tension_contexts=(
            TensionContext(
                layer=MusicalLayer.MELODY,
                altered=True,
                duration_beats=1,
                followed_by_step_to_chord_tone=True,
            ),
        ),
    ))
    assert result.interpretations.preferred.hypothesis_id == "g7alt"
    assert result.modal is not None
    assert result.local_key is not None
    assert len(result.tensions) == 1
    assert result.action_options


def test_high_ambiguity_keeps_multiple_interpretations_alive():
    result = reason_about_harmony(HarmonicReasoningInput(
        frame=dominant_frame(),
        hypotheses=(
            HarmonicHypothesis(
                "functional", "G7 dominant", function="dominant",
                interpretation_family="functional",
                confidence=ConfidenceVector(observed=.72, inferred=.68),
            ),
            HarmonicHypothesis(
                "modal", "G Mixolydian color", function="modal_tonic",
                interpretation_family="modal",
                confidence=ConfidenceVector(observed=.71, modal_context=.69),
            ),
        ),
    ))
    assert len(result.interpretations.ranked) == 2
    assert result.needs_more_evidence is True
    assert any("high_harmonic_ambiguity" in x.context_tags for x in result.action_options)


def test_resolution_debt_can_affect_current_action_options():
    debt = make_resolution_debt(
        voice_id="mel",
        source_pitch_midi=68,
        tendency="altered tension resolves",
        target_pitch_classes=(7,),
        urgency=.9,
    )
    result = reason_about_harmony(HarmonicReasoningInput(
        frame=dominant_frame(),
        hypotheses=(
            HarmonicHypothesis(
                "g7", "G7", function="dominant",
                confidence=ConfidenceVector(observed=.9, inferred=.9),
            ),
        ),
        voice_leading_context=VoiceLeadingContext(
            current=(VoiceState("mel", 68, VoiceRole.MELODY),),
            candidate=(VoiceState("mel", 67, VoiceRole.MELODY, TargetRole.GUIDE_TONE),),
            debts=(debt,),
        ),
    ))
    assert result.voice_leading.debt_resolution_credit > 0
    connect = next(x for x in result.action_options if x.intent is HarmonicIntent.CONNECT)
    assert "candidate can pay resolution debt" in connect.reasons


def test_reharmonization_is_optional_and_scored():
    proposal = make_substitute_dominant_proposal(
        proposal_id="db7",
        dominant_root_pc=7,
        target_root_pc=0,
        original_pitch_classes=(7, 11, 2, 5),
        substitute_pitch_classes=(1, 5, 8, 11),
        melody_pcs=(11,),
    )
    result = reason_about_harmony(HarmonicReasoningInput(
        frame=dominant_frame(),
        hypotheses=(
            HarmonicHypothesis(
                "g7", "G7", function="dominant",
                confidence=ConfidenceVector(expected=.9, observed=.9),
            ),
        ),
        reharmonization_proposals=(proposal,),
    ))
    assert len(result.reharmonizations) == 1
    assert any(x.option_id == "reharm:db7" for x in result.action_options)


def test_orchestrator_does_not_output_instrument_specific_or_fixed_future_notes():
    result = reason_about_harmony(HarmonicReasoningInput(frame=dominant_frame()))
    assert not hasattr(result, "future_notes")
    assert not hasattr(result, "future_chords")
    assert not hasattr(result, "left_hand")
    assert not hasattr(result, "bass_line")
    assert not hasattr(result, "drum_pattern")
