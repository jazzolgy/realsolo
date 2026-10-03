from realtime.ensemble_app.instrument_catalog import (
    InstrumentCapability,
    instrument_definition,
    is_baseline_instrument,
    normalize_instrument_label,
)


def test_new_baseline_instruments_are_known():
    for label in ("trumpet","guitar","electric bass","vocal","flute"):
        assert is_baseline_instrument(label)


def test_electric_bass_is_distinct_from_acoustic_bass():
    assert normalize_instrument_label("upright bass") == "acoustic_bass"
    assert normalize_instrument_label("bass guitar") == "electric_bass"


def test_vocal_aliases_normalize():
    assert normalize_instrument_label("voice") == "vocal"
    assert normalize_instrument_label("vocals") == "vocal"


def test_research_does_not_imply_generation():
    trumpet=instrument_definition("trumpet")
    assert trumpet is not None
    assert InstrumentCapability.RESEARCH in trumpet.capabilities
    assert InstrumentCapability.GENERATION not in trumpet.capabilities
