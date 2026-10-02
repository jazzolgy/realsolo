from music_intelligence.legends import VocabularyMemoryItem, VocabularyUseType
from players.drums.bebop import BebopPhraseMemory, SoloistEnergyProjection
from players.drums.bebop_runtime import (
    BebopRuntimeProjection,
    build_bebop_candidates,
    score_bebop_gesture,
)
from players.drums.legend_adapter import (
    drum_vocabulary_intent,
    vocabulary_gesture_adjustment,
)
from players.drums.model import (
    DrumGesture,
    DrumHit,
    DrummerRuntimeContext,
    DrummerSoftPlan,
    DrumVoice,
    GestureRole,
    Limb,
)


def memory(use_type, *, rhythm="", articulation="", recent=0):
    item = VocabularyMemoryItem(
        vocabulary_id="DR-MEM-1",
        source_id="recording.example",
        literal_representation="shared-private-literal",
        rhythm=rhythm,
        articulation=articulation,
        candidate_uses=frozenset({use_type}),
        recent_usage_count=recent,
        confidence=0.9,
        provenance=("shared_legend",),
    )
    return drum_vocabulary_intent(item, use_type=use_type)


def test_fragment_recall_prefers_phrase_related_current_gesture():
    intent = memory(VocabularyUseType.FRAGMENT_RECALL, rhythm="snare phrase")
    phrase = DrumGesture(
        hits=(DrumHit(DrumVoice.SNARE, Limb.LEFT_HAND, 65),),
        role=GestureRole.COMP,
        tags=frozenset({"snare_phrase", "return"}),
    )
    unrelated = DrumGesture(
        hits=(DrumHit(DrumVoice.RIDE, Limb.RIGHT_HAND, 65),),
        role=GestureRole.TIME,
        tags=frozenset({"ride_continuity"}),
    )
    p, _ = vocabulary_gesture_adjustment(phrase, (intent,))
    u, _ = vocabulary_gesture_adjustment(unrelated, (intent,))
    assert p > u


def test_hybrid_memory_can_affect_runtime_without_future_phrase():
    intent = memory(VocabularyUseType.HYBRID_COMPOSITION, rhythm="snare phrase")
    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"}))
    context = DrummerRuntimeContext(position_in_bar_beats=1.0, tempo_bpm=180)
    base = BebopRuntimeProjection(
        soloist=SoloistEnergyProjection(0.45, 0.5, 0.0),
        phrase_memory=BebopPhraseMemory(),
    )
    with_memory = BebopRuntimeProjection(
        soloist=base.soloist,
        phrase_memory=base.phrase_memory,
        vocabulary_intents=(intent,),
    )
    candidate = next(
        g for g in build_bebop_candidates(plan, context, base)
        if "snare_phrase" in g.tags
    )
    plain = score_bebop_gesture(candidate, plan, context, base)
    remembered = score_bebop_gesture(candidate, plan, context, with_memory)
    assert remembered.score > plain.score
    assert any(name.startswith("vocabulary:") for name, _ in remembered.components)
    assert not hasattr(intent, "future_hits")
    assert not hasattr(intent, "future_phrase")


def test_recent_vocabulary_overuse_reduces_current_candidate_influence():
    fresh = memory(VocabularyUseType.ABSTRACTED_PATTERN, rhythm="ride continuity", recent=0)
    stale = memory(VocabularyUseType.ABSTRACTED_PATTERN, rhythm="ride continuity", recent=8)
    ride = DrumGesture(
        hits=(DrumHit(DrumVoice.RIDE, Limb.RIGHT_HAND, 70),),
        role=GestureRole.TIME,
        tags=frozenset({"ride_continuity"}),
    )
    fresh_score, _ = vocabulary_gesture_adjustment(ride, (fresh,))
    stale_score, _ = vocabulary_gesture_adjustment(ride, (stale,))
    assert fresh_score > stale_score


def test_literal_quote_does_not_bonus_unmarked_generated_gesture():
    literal = memory(VocabularyUseType.LITERAL_QUOTE)
    generated = DrumGesture(
        hits=(DrumHit(DrumVoice.SNARE, Limb.LEFT_HAND, 70),),
        role=GestureRole.COMP,
        tags=frozenset({"snare_phrase", "variation"}),
    )
    delta, _ = vocabulary_gesture_adjustment(generated, (literal,))
    # Legal to quote, but generated material does not masquerade as a quote.
    assert delta < 0.2
