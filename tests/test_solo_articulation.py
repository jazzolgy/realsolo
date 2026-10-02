from realtime.ensemble_app.solo_articulation import (
    SoloArticulation,
    SoloRenderIntent,
    canonical_solo_articulations,
    choose_sample_family,
)


def test_solo_articulation_aliases_are_renderer_neutral():
    arts = canonical_solo_articulations(("staccato", "late_vibrato", "breath"))
    assert SoloArticulation.SHORT in arts
    assert SoloArticulation.VIBRATO in arts
    assert SoloArticulation.BREATHY in arts


def test_sample_family_prefers_explicit_color():
    intent = SoloRenderIntent(
        "tenor_sax", 62, 82, .75,
        articulation=(SoloArticulation.SUBTONE, SoloArticulation.VIBRATO),
    )
    assert choose_sample_family(intent) == "subtone"


def test_plain_solo_defaults_to_sustain():
    assert canonical_solo_articulations(()) == (SoloArticulation.SUSTAIN,)
