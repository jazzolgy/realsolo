from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)
from players.bass import BassContext, BassMode, generate_immediate_bass_candidates
from players.bass.interaction_grammar import BassInteractionDecision, BassInteractionIntent
from players.bass.performance_memory import BassPerformanceSnapshot
from players.bass.phrase_intent import (
    BassPhraseContext,
    BassPhraseIntentKind,
    choose_bass_phrase_intent,
)


def ev(root, symbol, pcs):
    return HarmonicEvidence(
        source=HarmonySource.EXPECTED,
        root_pc=root,
        symbol=symbol,
        pitch_classes=frozenset(pcs),
    )


def best(items, role):
    vals=[x.score for x in items if x.harmonic_role.value == role]
    assert vals
    return max(vals)


def candidate(items, role):
    vals=[x for x in items if x.harmonic_role.value == role]
    assert vals
    return max(vals, key=lambda x:x.score)


def test_explicit_phrase_progress_moves_ground_develop_build_release():
    kinds=[]
    for progress in (.05,.35,.70,.92):
        intent=choose_bass_phrase_intent(
            BassPhraseContext(phrase_progress=progress)
        )
        kinds.append(intent.kind)
    assert kinds == [
        BassPhraseIntentKind.GROUND,
        BassPhraseIntentKind.DEVELOP,
        BassPhraseIntentKind.BUILD,
        BassPhraseIntentKind.RELEASE,
    ]


def test_phrase_intention_changes_candidate_ranking_without_future_notes():
    frame=HarmonicFrame(
        expected=ev(0,"Cm7",{0,3,7,10}),
        next_expected=ev(5,"F7",{5,9,0,3}),
    )
    ground=choose_bass_phrase_intent(BassPhraseContext(phrase_progress=.05))
    build=choose_bass_phrase_intent(BassPhraseContext(phrase_progress=.70))
    common=dict(
        mode=BassMode.WALKING,
        beat_in_measure=1.0,
        previous_pitch_midi=36,
        local_key_pitch_classes=frozenset({0,2,3,5,7,9,10}),
    )
    g=generate_immediate_bass_candidates(frame,BassContext(**common,phrase_intent=ground))
    b=generate_immediate_bass_candidates(frame,BassContext(**common,phrase_intent=build))
    assert best(g,"root") > best(b,"root")
    assert best(b,"diatonic_passing") > best(g,"diatonic_passing")


def test_phrase_build_and_release_change_note_body():
    frame=HarmonicFrame(expected=ev(0,"Cm7",{0,3,7,10}))
    build=choose_bass_phrase_intent(BassPhraseContext(phrase_progress=.70))
    release=choose_bass_phrase_intent(BassPhraseContext(phrase_progress=.92))
    common=dict(
        mode=BassMode.WALKING,
        beat_in_measure=0.0,
        previous_pitch_midi=36,
    )
    b=candidate(generate_immediate_bass_candidates(frame,BassContext(**common,phrase_intent=build)),"root")
    r=candidate(generate_immediate_bass_candidates(frame,BassContext(**common,phrase_intent=release)),"root")
    assert b.expression.accent > r.expression.accent
    assert b.expression.microtiming_ms < r.expression.microtiming_ms


def test_phrase_intent_persists_when_no_new_evidence_requires_replan():
    first=choose_bass_phrase_intent(BassPhraseContext())
    second=choose_bass_phrase_intent(
        BassPhraseContext(),
        previous=first,
        actions_under_previous=1,
    )
    assert second is first
