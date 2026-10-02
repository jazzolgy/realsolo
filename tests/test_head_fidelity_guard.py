from music_intelligence.reasoning.head_fidelity import (
    HeadFidelityContext,
    HeadFidelityMode,
    enforce_head_fidelity,
    generate_head_candidate_variants,
)
from music_intelligence.reasoning.legend_style_core import CandidateEvent
from players.piano.head_interpretation import (
    HeadInterpretationContext,
    head_event_candidates,
    interpret_head_event,
)


def test_natural_head_keeps_strong_beat_written_pitch_exact():
    written=CandidateEvent(67,1.0,tags=frozenset({"written"}))
    proposed=CandidateEvent(62,.25,onset_offset_beats=.30,tags=frozenset({"wild"}))
    guarded=enforce_head_fidelity(
        written,
        proposed,
        HeadFidelityContext(
            mode=HeadFidelityMode.NATURAL,
            strong_beat=True,
        ),
    )
    assert guarded.pitch_midi==67
    assert guarded.duration_beats>=.48
    assert abs(guarded.onset_offset_beats)<=.14
    assert "head_structural_pitch_locked" in guarded.tags


def test_natural_head_allows_only_nearby_ornaments_on_weak_notes():
    written=CandidateEvent(67,.5)
    variants=generate_head_candidate_variants(
        written,
        HeadFidelityContext(
            mode=HeadFidelityMode.NATURAL,
            strong_beat=False,
            phrase_anchor=False,
            harmonic_pitch_classes=frozenset({0,4,7,11}),
        ),
    )
    pitches={x.pitch_midi for x in variants if x.pitch_midi is not None}
    assert 67 in pitches
    assert all(abs(p-67)<=2 for p in pitches)
    assert not any(abs(p-67)>=5 for p in pitches)


def test_natural_head_supports_repeat_and_split_without_recomposing_pitch():
    written=CandidateEvent(64,1.0)
    variants=generate_head_candidate_variants(
        written,
        HeadFidelityContext(mode=HeadFidelityMode.NATURAL),
    )
    repeat=[x for x in variants if "head_rhythmic_repeat" in x.tags]
    split=[x for x in variants if "head_rhythmic_split" in x.tags]
    assert repeat and split
    assert all(x.pitch_midi==64 for x in repeat+split)
    assert all(x.duration_beats<1.0 for x in repeat+split)


def test_strict_head_has_no_pitch_substitution_candidates():
    written=CandidateEvent(70,.75)
    variants=generate_head_candidate_variants(
        written,
        HeadFidelityContext(mode=HeadFidelityMode.STRICT),
    )
    assert len(variants)==1
    assert variants[0].pitch_midi==70


def test_piano_head_interpretation_preserves_written_frame_pitch():
    written=CandidateEvent(69,1.0,onset_offset_beats=0.0)
    interpreted=interpret_head_event(
        written,
        HeadInterpretationContext(
            tempo_bpm=130.0,
            phrase_maturity=.8,
            phrase_end_pressure=.9,
            next_harmony_known=True,
            strong_beat=True,
            phrase_anchor=True,
            fidelity_mode=HeadFidelityMode.NATURAL,
        ),
    )
    assert interpreted.pitch_midi==69
    assert "written_pitch_preserved" in interpreted.tags


def test_piano_head_candidates_remain_bounded_around_written_note():
    written=CandidateEvent(65,1.0)
    variants=head_event_candidates(
        written,
        HeadInterpretationContext(
            tempo_bpm=130.0,
            fidelity_mode=HeadFidelityMode.NATURAL,
            strong_beat=False,
            phrase_anchor=False,
            previous_written_pitch_midi=64,
            next_written_pitch_midi=67,
            harmonic_pitch_classes=frozenset({0,4,5,7,9}),
        ),
    )
    assert variants
    assert any(v.source_family=="head_written" for v in variants)
    assert all(
        v.pitch_midi is None or abs(v.pitch_midi-65)<=2
        for v in variants
    )
    assert not any("large_leap" in v.tags for v in variants)
