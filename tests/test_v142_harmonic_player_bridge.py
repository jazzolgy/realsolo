from music_intelligence.harmony.hypothesis_engine import ConfidenceVector, HarmonicHypothesis
from music_intelligence.harmony.jazz_harmony_core import HarmonicEvidence, HarmonicFrame, HarmonySource
from music_intelligence.harmony.orchestrator import HarmonicReasoningInput, reason_about_harmony
from music_intelligence.reasoning.harmonic_player_bridge import (
    apply_harmonic_guidance_to_monophonic_score,
    harmonic_guidance_for_candidate,
    rerank_monophonic_with_harmony,
)
from music_intelligence.reasoning.legend_style_core import CandidateEvent, CandidateScore


def dominant_harmony(ambiguity=False):
    hypotheses = (
        HarmonicHypothesis(
            "g7", "G7 dominant", function="dominant",
            interpretation_family="functional",
            confidence=ConfidenceVector(observed=.9, inferred=.9),
        ),
    )
    if ambiguity:
        hypotheses += (
            HarmonicHypothesis(
                "modal", "G Mixolydian",
                function="modal_tonic",
                interpretation_family="modal",
                confidence=ConfidenceVector(observed=.88, modal_context=.89),
            ),
        )
    return reason_about_harmony(HarmonicReasoningInput(
        frame=HarmonicFrame(
            expected=HarmonicEvidence(
                HarmonySource.EXPECTED, symbol="G7", root_pc=7, function="dominant"
            ),
            inferred=HarmonicEvidence(
                HarmonySource.INFERRED, symbol="G7alt", root_pc=7, function="dominant"
            ),
            next_expected=HarmonicEvidence(
                HarmonySource.EXPECTED, symbol="Cmaj7", root_pc=0, function="tonic"
            ),
            tension=.75,
        ),
        hypotheses=hypotheses,
    ))


def test_guide_tone_candidate_gets_shared_harmonic_support():
    harmony = dominant_harmony()
    c = CandidateEvent(59, .5, tags=frozenset({"guide_tone", "resolution_path"}))
    g = harmonic_guidance_for_candidate(c, harmony)
    assert g.score_delta > 0
    assert g.matched_option_ids


def test_altered_candidate_can_match_intensify_affordance():
    harmony = dominant_harmony()
    c = CandidateEvent(70, .5, tags=frozenset({"altered", "sharp9", "directed_target"}))
    g = harmonic_guidance_for_candidate(c, harmony)
    assert g.score_delta > 0
    assert any("dominant.altered_color" in x for x in g.matched_option_ids)


def test_unrelated_candidate_is_not_forced_by_harmony():
    harmony = dominant_harmony()
    c = CandidateEvent(60, .5, tags=frozenset({"breath_noise"}))
    g = harmonic_guidance_for_candidate(c, harmony)
    assert g.score_delta == 0
    assert g.matched_option_ids == ()


def test_guidance_is_additive_not_replacement_of_player_score():
    harmony = dominant_harmony()
    base = CandidateScore(
        CandidateEvent(59, .5, tags=frozenset({"guide_tone"})),
        .42,
        {"player_style": .42},
        ("player-specific choice",),
    )
    out = apply_harmonic_guidance_to_monophonic_score(base, harmony)
    assert out.total > base.total
    assert out.components["player_style"] == .42
    assert "player-specific choice" in out.reasons


def test_reranking_can_change_player_choice_without_generating_notes():
    harmony = dominant_harmony()
    plain = CandidateScore(CandidateEvent(60, .5, tags=frozenset({"ornament"})), .20)
    directed = CandidateScore(
        CandidateEvent(59, .5, tags=frozenset({"guide_tone", "resolution_path"})),
        .12,
    )
    ranked = rerank_monophonic_with_harmony((plain, directed), harmony)
    assert ranked[0].candidate == directed.candidate


def test_ambiguity_dampens_harmonic_bias():
    clear = dominant_harmony(False)
    ambiguous = dominant_harmony(True)
    c = CandidateEvent(59, .5, tags=frozenset({"guide_tone", "resolution_path"}))
    assert harmonic_guidance_for_candidate(c, clear).score_delta >= harmonic_guidance_for_candidate(c, ambiguous).score_delta


def test_bridge_does_not_generate_future_notes_or_instrument_realization():
    harmony = dominant_harmony()
    c = CandidateEvent(59, .5, tags=frozenset({"guide_tone"}))
    g = harmonic_guidance_for_candidate(c, harmony)
    assert not hasattr(g, "future_notes")
    assert not hasattr(g, "voicing")
    assert not hasattr(g, "bass_line")
    assert not hasattr(g, "drum_pattern")
