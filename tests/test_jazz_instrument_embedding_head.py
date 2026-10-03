import numpy as np

from realtime.ensemble_app.jazz_instrument_embedding_head import JazzInstrumentEmbeddingHead


def test_head_does_not_bootstrap_ambiguous_example(tmp_path):
    head=JazzInstrumentEmbeddingHead(tmp_path/"head.json")
    added=head.observe(
        "trumpet",
        np.array([1.0,0.0,0.0],dtype=np.float32),
        confidence=.80,
        margin=.30,
    )
    assert added is False
    assert head.counts()=={}


def test_head_bootstraps_strict_high_confidence_examples_and_persists(tmp_path):
    path=tmp_path/"head.json"
    head=JazzInstrumentEmbeddingHead(path,min_examples=2)
    for _ in range(2):
        assert head.observe(
            "trumpet",
            np.array([1.0,.05,0.0],dtype=np.float32),
            confidence=.96,
            margin=.40,
        )
        assert head.observe(
            "saxophone",
            np.array([.02,1.0,.05],dtype=np.float32),
            confidence=.95,
            margin=.35,
        )
    probs=head.predict(np.array([.98,.03,0.0],dtype=np.float32))
    assert probs["trumpet"] > probs["saxophone"]

    restored=JazzInstrumentEmbeddingHead(path,min_examples=2)
    assert restored.counts()["trumpet"]==2
    probs2=restored.predict(np.array([.98,.03,0.0],dtype=np.float32))
    assert probs2["trumpet"] > probs2["saxophone"]


def test_explicit_label_can_be_admitted_below_bootstrap_threshold():
    head=JazzInstrumentEmbeddingHead(None,min_examples=1)
    assert head.observe(
        "flute",
        np.array([0.0,0.0,1.0],dtype=np.float32),
        confidence=.2,
        margin=.01,
        explicit_label=True,
    )
    assert head.counts()["flute"]==1
