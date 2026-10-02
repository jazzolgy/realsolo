from music_intelligence.harmony.hypothesis_engine import (
    ConfidenceVector,
    EvidenceChannel,
    HarmonicHypothesis,
    merge_human_correction,
    rank_harmonic_hypotheses,
)


def h(hid, label, **kwargs):
    return HarmonicHypothesis(
        hid,
        label,
        confidence=ConfidenceVector(**kwargs),
    )


def test_multiple_harmonic_analyses_are_preserved():
    result = rank_harmonic_hypotheses((
        h("modal", "D Dorian tonic", observed=.75, bass=.9, modal_context=.9),
        h("tonal", "ii in C major", observed=.75, inferred=.55, form=.3),
    ))
    assert result.preferred is not None
    assert len(result.alternatives) == 1
    assert {x.hypothesis.label for x in result.ranked} == {
        "D Dorian tonic", "ii in C major"
    }


def test_bass_and_modal_context_can_disambiguate_same_surface():
    modal = HarmonicHypothesis(
        "modal", "D Dorian tonic", root_pc=2, interpretation_family="modal",
        confidence=ConfidenceVector(observed=.7, bass=.95, modal_context=.95),
    )
    tonal = HarmonicHypothesis(
        "tonal", "ii in C major", root_pc=2, interpretation_family="functional",
        confidence=ConfidenceVector(observed=.7, bass=.25, modal_context=.15, form=.4),
    )
    result = rank_harmonic_hypotheses((modal, tonal))
    assert result.preferred.hypothesis_id == "modal"


def test_contradiction_penalty_does_not_delete_alternative():
    clean = HarmonicHypothesis(
        "a", "clean",
        confidence=ConfidenceVector(observed=.7, inferred=.7),
    )
    conflicted = HarmonicHypothesis(
        "b", "conflicted",
        confidence=ConfidenceVector(observed=.8, inferred=.8),
        contradictions=("bass disagrees", "cadence disagrees"),
    )
    result = rank_harmonic_hypotheses((clean, conflicted))
    assert len(result.ranked) == 2
    b = next(x for x in result.ranked if x.hypothesis.hypothesis_id == "b")
    assert b.contradiction_penalty > 0


def test_close_hypotheses_report_need_for_more_evidence():
    result = rank_harmonic_hypotheses((
        h("a", "A", observed=.70, inferred=.65),
        h("b", "B", observed=.69, inferred=.66),
    ))
    assert result.needs_more_evidence is True
    assert result.ambiguity > .9


def test_strongly_separated_hypotheses_can_be_actionable():
    result = rank_harmonic_hypotheses((
        h("a", "A", observed=.95, inferred=.9, bass=.95, form=.9),
        h("b", "B", observed=.2, inferred=.2, bass=.1, form=.1),
    ))
    assert result.preferred.hypothesis_id == "a"
    assert result.top_margin > .5
    assert result.needs_more_evidence is False


def test_channel_weights_allow_context_sensitive_evidence_priority():
    hypotheses = (
        h("chart", "chart", expected=.95, observed=.3),
        h("heard", "heard", expected=.2, observed=.9),
    )
    heard = rank_harmonic_hypotheses(
        hypotheses,
        channel_weights={
            EvidenceChannel.EXPECTED: .4,
            EvidenceChannel.OBSERVED: 1.5,
        },
    )
    assert heard.preferred.hypothesis_id == "heard"


def test_human_correction_is_preserved_not_destructively_overwritten():
    original = h("x", "G7", expected=.8, observed=.7)
    corrected = merge_human_correction(
        original,
        correction="hear as Db7/G tritone relation",
        confidence=.95,
    )
    assert corrected.human_correction is not None
    assert corrected.confidence.expected == original.confidence.expected
    assert corrected.confidence.observed == original.confidence.observed
    assert corrected.confidence.human == .95
    assert "human_correction" in corrected.provenance


def test_no_single_required_scale_or_future_sequence():
    result = rank_harmonic_hypotheses((h("a", "A", observed=.8),))
    assert not hasattr(result, "required_scale")
    assert not hasattr(result, "future_chords")
    assert not hasattr(result, "future_notes")
