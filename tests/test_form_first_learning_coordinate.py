import pytest

from music_intelligence.learning import (
    LearningDomain,
    MusicalScoreCoordinate,
    PerformancePhase,
    SharedLearningEngine,
    StructuralPerformanceData,
    StructuralPerformanceEvent,
    extract_learning_artifacts,
)


def pos(*,chorus=2,bar=21,beat=3.0):
    return MusicalScoreCoordinate(
        song_id="autumn_leaves",
        section="B",
        bar=bar,
        beat=beat,
        form_length_bars=32,
        form_bar=bar,
        chorus_index=chorus,
        performance_phase=PerformancePhase.SOLO,
        phrase_position="phrase_end",
        harmonic_function="ii_v_motion",
        arrangement_segment="core_form",
        within_core_form=True,
    )


def event(eid,onset,audio_s,*,chorus=2,bar=21,beat=3.0,role="solo"):
    return StructuralPerformanceEvent(
        eid,onset,.5,60,
        instrument="piano",
        role=role,
        phrase_id="p1" if role=="solo" else "",
        audio_onset_s=audio_s,
        audio_offset_s=audio_s+.2,
        musical_position=pos(chorus=chorus,bar=bar,beat=beat),
    )


def test_canonical_event_key_ignores_elapsed_audio_time():
    a=event("a",0.0,83.417)
    b=event("b",0.0,842.310)
    assert a.canonical_position_key==b.canonical_position_key


def test_form_first_dataset_can_require_musical_coordinates():
    unaligned=StructuralPerformanceEvent("x",0,.5,60)
    data=StructuralPerformanceData(
        source_id="x",
        events=(unaligned,),
        require_musical_coordinates=True,
    )
    with pytest.raises(ValueError,match="musical_position is required"):
        data.validate()


def test_learning_artifacts_carry_form_bar_beat_and_chorus():
    data=StructuralPerformanceData(
        source_id="be.aligned",
        events=(
            event("a",0.0,83.4,beat=3.0),
            event("b",.5,83.7,beat=3.5),
            event("c",1.0,84.0,beat=4.0),
        ),
        tempo_bpm=200,
        meter="4/4",
        form_label="32_bar",
        require_musical_coordinates=True,
    )
    artifacts=extract_learning_artifacts(data)
    motif=next(x for x in artifacts if x.domain is LearningDomain.MOTIF)
    assert motif.musical_position is not None
    assert motif.features["form_bar"]==21
    assert motif.features["chorus_index"]==2
    assert motif.features["section"]=="B"


def test_aligned_artifact_updates_evidence_prior():
    data=StructuralPerformanceData(
        source_id="be.aligned",
        events=(
            event("a",0.0,83.4,beat=3.0),
            event("b",.5,83.7,beat=3.5),
            event("c",1.0,84.0,beat=4.0),
        ),
        require_musical_coordinates=True,
    )
    artifacts=extract_learning_artifacts(data)
    engine=SharedLearningEngine()
    engine.ingest_artifacts(artifacts,learn=False,study_as_evidence=True)
    assert engine.evidence_prior(LearningDomain.MOTIF).observations>0
