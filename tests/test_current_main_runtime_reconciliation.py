from dataclasses import dataclass

from music_intelligence.audio_evidence import artifacts_from_audio_aggregate
from music_intelligence.corpus.realchord import (
    RealChordChord,
    RealChordMeasure,
    RealChordSong,
)
from music_intelligence.expression import ExpressiveContext
from music_intelligence.learning import (
    PerformancePhase,
    coordinate_from_listener_estimate,
)
from music_intelligence.learning.audio_evidence import (
    artifacts_from_audio_aggregate as implementation_audio_adapter,
)
from music_intelligence.legends.interfaces import (
    VocabularyQuery,
    VocabularyUseType,
)
from music_intelligence.reasoning import (
    build_canonical_runtime_context,
    legend_runtime_resources,
)


@dataclass(frozen=True)
class Estimate:
    measure_index: int | None
    beat_in_measure: float | None
    section_id: str | None
    section_measure_index: int | None
    form_iteration: int | None
    confidence: float


def test_listener_estimate_adapts_to_only_canonical_coordinate():
    p=coordinate_from_listener_estimate(
        Estimate(0,1.5,"A",0,2,.88),
        song_id="Autumn Leaves",
        score_source_id="realchord:autumn-leaves",
        realchord_id="autumn-leaves",
        form_length_bars=32,
        performance_phase=PerformancePhase.SOLO,
    )
    assert p.bar==1
    assert p.form_bar==1
    assert p.beat==1.5
    assert p.chorus_index==2
    assert p.realchord_id=="autumn-leaves"
    assert not hasattr(p,"onset_sec")


def test_legend_profile_and_vocabulary_availability_are_independent():
    evans=legend_runtime_resources("bill_evans")
    assert not evans.profile_available
    assert evans.vocabulary_available(target_instrument="piano")

    parker=legend_runtime_resources("charlie_parker")
    assert parker.profile_available
    assert not parker.vocabulary_available(target_instrument="sax")


def test_runtime_bridge_consumes_realchord_expression_and_vocabulary_without_duplication():
    song=RealChordSong(
        realchord_id="autumn-leaves",
        title="Autumn Leaves",
        key="G-",
        form="32-bar",
        measures=(
            RealChordMeasure(
                measure=1,
                section="A1",
                chords=(RealChordChord(beat=1.0,symbol="Cm7"),),
            ),
        ),
    )
    p=coordinate_from_listener_estimate(
        Estimate(0,1.0,"A1",0,0,.95),
        song_id="Autumn Leaves",
        score_source_id="realchord:autumn-leaves",
        realchord_id="autumn-leaves",
        form_length_bars=32,
        performance_phase=PerformancePhase.SOLO,
    )
    query=VocabularyQuery(
        legend_id="bill_evans",
        target_instrument="piano",
        allowed_uses=frozenset(VocabularyUseType),
        limit=4,
    )
    ctx=build_canonical_runtime_context(
        position=p,
        expressive_context=ExpressiveContext(
            position=p,
            tension=.55,
            ensemble_density=.45,
            target_foreground_weight=.7,
        ),
        realchord_song=song,
        legend_id="bill_evans",
        vocabulary_query=query,
        vocabulary_opportunity_index=0,
    )
    assert ctx.expected_harmony is not None
    assert ctx.expected_harmony.chord_symbol=="Cm7"
    assert ctx.expressive_intent.foreground_weight>=.69
    assert ctx.vocabulary
    # Current public Evans vocabulary is abstract-only, so a nominal direct
    # 30% slot must fall back rather than fabricate a literal quote.
    assert ctx.vocabulary[0].use_type is not VocabularyUseType.LITERAL_QUOTE


def test_audio_evidence_public_facade_is_alias_not_second_engine():
    assert artifacts_from_audio_aggregate is implementation_audio_adapter
