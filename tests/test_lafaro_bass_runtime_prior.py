from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)
from music_intelligence.legends.scott_lafaro import SCOTT_LAFARO_PROFILE_VIEW
from music_intelligence.reasoning.legend_style_core import CandidateEvent
from music_intelligence.reasoning.solo_grammar import SoloDevelopmentOperation
from players.bass import BassMode, BassSequentialRunner, BassStepInput


def ev(root, symbol, pcs):
    return HarmonicEvidence(
        source=HarmonySource.EXPECTED,
        root_pc=root,
        symbol=symbol,
        pitch_classes=frozenset(pcs),
    )


def frame():
    return HarmonicFrame(
        expected=ev(2, "Dm7", {2, 5, 9, 0}),
        next_expected=ev(7, "G7", {7, 11, 2, 5}),
    )


def seed(runner):
    for pitch in (40, 43, 45, 48):
        runner.solo_memory.commit(
            CandidateEvent(pitch, .5, source_family="test_seed"),
            SoloDevelopmentOperation.STATE,
        )


def test_lafaro_prior_reweights_actual_bass_solo_operation_choice():
    generic = BassSequentialRunner()
    lafaro = BassSequentialRunner()
    seed(generic)
    seed(lafaro)

    common = dict(
        frame=frame(),
        mode=BassMode.SOLO,
        beat_in_measure=1.0,
        absolute_beat=1.0,
        phrase_progress=.45,
        local_key_pitch_classes=frozenset({0,2,4,5,7,9,10}),
    )
    g = generic.step(BassStepInput(**common))
    l = lafaro.step(BassStepInput(
        **common,
        legend_profile=SCOTT_LAFARO_PROFILE_VIEW,
    ))

    assert g.solo_plan is not None
    assert l.solo_plan is not None
    assert g.solo_plan.operation is SoloDevelopmentOperation.VARY
    assert l.solo_plan.operation is SoloDevelopmentOperation.REPEAT
    assert g.candidate.event.source_family.startswith("bass_solo:")
    assert l.candidate.event.source_family.startswith("bass_solo:")
