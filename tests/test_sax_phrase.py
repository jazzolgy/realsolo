from players.sax import SaxPhraseContext, SaxPhraseMemory


def test_stepwise_short_notes_connect_legato():
    memory = SaxPhraseMemory()
    context = SaxPhraseContext(62, 60, .5, 1.0, .35)
    decision = memory.decide(context)
    assert decision.connect_legato
    assert decision.soften_attack


def test_breath_inserted_after_long_run():
    memory = SaxPhraseMemory(notes_since_breath=7, beats_since_breath=5.6, last_pitch_midi=64)
    context = SaxPhraseContext(65, 64, .5, 0.0, .1)
    decision = memory.decide(context)
    assert decision.breath_before
    assert not decision.connect_legato


def test_phrase_end_opens_release():
    memory = SaxPhraseMemory()
    context = SaxPhraseContext(69, 67, 1.0, 3.0, .95)
    decision = memory.decide(context)
    assert decision.phrase_end
    assert decision.release_shape == "open"
