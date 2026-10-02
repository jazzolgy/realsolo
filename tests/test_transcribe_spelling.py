from music_intelligence.transcribe import PerformedPitch
from music_intelligence.transcribe.spelling import (
    AccidentalPreference,
    PitchSpellingContext,
    preferred_spelling,
    spelling_candidates,
)


def test_flat_key_context_prefers_db_over_c_sharp():
    pitch = PerformedPitch(nominal_midi=61)
    best = preferred_spelling(pitch, PitchSpellingContext(key_fifths=-4))
    assert best.written_pitch.name == "Db4"


def test_sharp_key_context_prefers_f_sharp_over_g_flat():
    pitch = PerformedPitch(nominal_midi=66)
    best = preferred_spelling(pitch, PitchSpellingContext(key_fifths=3))
    assert best.written_pitch.name == "F#4"


def test_explicit_shared_context_can_override_generic_accidental_preference():
    pitch = PerformedPitch(nominal_midi=70)
    context = PitchSpellingContext(
        key_fifths=4,
        explicit_pitch_class_spellings=((10, "Bb"),),
    )
    best = preferred_spelling(pitch, context)
    assert best.written_pitch.name == "Bb4"
    assert "explicit Shared Core / human spelling preference" in best.reasons


def test_spelling_keeps_alternatives_instead_of_collapsing_to_one_answer():
    candidates = spelling_candidates(
        PerformedPitch(nominal_midi=61),
        PitchSpellingContext(accidental_preference=AccidentalPreference.AUTO),
    )
    names = {c.written_pitch.name for c in candidates}
    assert "C#4" in names
    assert "Db4" in names
    assert len(candidates) >= 2


def test_continuous_pitch_without_nominal_pitch_is_not_forced_into_western_spelling():
    pitch = PerformedPitch(
        frequency_hz=277.18,
        continuous_pitch_ref="curve:traditional:1",
    )
    try:
        preferred_spelling(pitch)
    except ValueError as exc:
        assert "nominal_midi" in str(exc)
    else:
        raise AssertionError("continuous pitch must not be prematurely reduced")
