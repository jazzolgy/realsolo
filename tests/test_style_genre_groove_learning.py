from pathlib import Path
from music_intelligence.corpus.registry import CorpusAccess,CorpusItem,CorpusKind,CorpusUse,RightsProfile
from music_intelligence.learning import (
    LearningDomain,LearningFeedback,SharedLearningEngine,
    StructuralPerformanceData,StructuralPerformanceEvent,convert_audio_to_learning_data,
)

class FunkAnalyzer:
    def analyze(self,audio_path,*,source_item):
        ev=[]
        # Strong 2/4 backbeat plus syncopated sixteenth activity.
        for i,(beat,inst,accent,role) in enumerate((
            (0.0,"bass",.7,"solo"),(.75,"bass",.55,"solo"),
            (1.0,"drums",.95,"comping"),(1.5,"piano",.5,"comping"),
            (2.0,"bass",.7,"solo"),(2.75,"bass",.55,"solo"),
            (3.0,"drums",.95,"comping"),(3.5,"piano",.5,"comping"),
        )):
            ev.append(StructuralPerformanceEvent(
                f"e{i}",beat,.25,60+i if inst!="drums" else None,
                unpitched_token="snare" if inst=="drums" else "",
                instrument=inst,role=role,dynamic=.6,accent=accent,
                harmony_label="E7",phrase_id="p1" if role=="solo" else "",
                ensemble_role="foreground" if role=="solo" else "support",
                tags=frozenset({role}),
            ))
        return StructuralPerformanceData(
            source_id=source_item.item_id,events=tuple(ev),tempo_bpm=104,meter="4/4",
            metadata={"genre_label":"funk","rhythm_label":"16th_funk","style_label":"test_band"}
        )

def item(permission=True):
    return CorpusItem(
        item_id="audio.funk.test",kind=CorpusKind.MUSICAL_INTELLIGENCE,
        media_type="audio/mpeg",title="funk test",local_relpath="audio/funk.mp3",
        access=CorpusAccess.LOCAL_PRIVATE,
        uses=frozenset({CorpusUse.TRAINING,CorpusUse.RESEARCH}),
        rights=RightsProfile(training_permission=True if permission else None,research_permission=True),
    )

def test_style_genre_and_groove_artifacts_are_created():
    c=convert_audio_to_learning_data(item(),Path("x.mp3"),FunkAnalyzer())
    domains={a.domain for a in c.artifacts}
    assert LearningDomain.STYLE in domains
    assert LearningDomain.GENRE in domains
    assert LearningDomain.RHYTHM_GROOVE in domains
    groove=next(a for a in c.artifacts if a.domain is LearningDomain.RHYTHM_GROOVE)
    assert groove.features["rhythm_label"]=="16th_funk"
    assert groove.features["backbeat_strength"]>.8
    assert groove.features["syncopation_rate"]>0

def test_shared_engine_learns_genre_and_groove_priors():
    c=convert_audio_to_learning_data(item(),Path("x.mp3"),FunkAnalyzer())
    engine=SharedLearningEngine()
    engine.ingest_conversion(c)
    gp=engine.prior(LearningDomain.GENRE)
    rp=engine.prior(LearningDomain.RHYTHM_GROOVE)
    assert gp.category_weight("genre_label","funk")==1.0
    assert rp.category_weight("rhythm_label","16th_funk")==1.0
    assert rp.observations==1

def test_feedback_updates_runtime_bias():
    engine=SharedLearningEngine()
    engine.record_feedback(LearningFeedback(LearningDomain.RHYTHM_GROOVE,"syncopation_rate",.9))
    assert engine.prior(LearningDomain.RHYTHM_GROOVE).feedback_bias["syncopation_rate"]>0

def test_rights_gate_stores_derived_but_does_not_train():
    c=convert_audio_to_learning_data(item(False),Path("x.mp3"),FunkAnalyzer())
    engine=SharedLearningEngine()
    engine.ingest_conversion(c)
    assert len(engine.store)>0
    assert engine.prior(LearningDomain.GENRE).observations==0
