from pathlib import Path

from music_intelligence.corpus.registry import (
    CorpusAccess,CorpusItem,CorpusKind,CorpusUse,RightsProfile,
)
from music_intelligence.learning import (
    LearningDisposition,LearningDomain,StructuralPerformanceData,
    StructuralPerformanceEvent,convert_audio_to_learning_data,
)


class FakeAnalyzer:
    def analyze(self,audio_path,*,source_item):
        return StructuralPerformanceData(
            source_id=source_item.item_id,
            tempo_bpm=180,
            meter="4/4",
            form_label="AABA",
            events=(
                StructuralPerformanceEvent("e1",0,.5,60,instrument="piano",role="solo",dynamic=.5,accent=.5,harmony_label="Dm7",phrase_id="p1",ensemble_role="foreground"),
                StructuralPerformanceEvent("e2",.5,.5,62,instrument="piano",role="solo",dynamic=.58,accent=.7,harmony_label="Dm7",phrase_id="p1",ensemble_role="foreground",timing_offset_beats=.02),
                StructuralPerformanceEvent("e3",1,.5,63,instrument="piano",role="solo",dynamic=.62,accent=.6,harmony_label="G7",phrase_id="p1",ensemble_role="foreground"),
                StructuralPerformanceEvent("e4",1.5,.5,67,instrument="piano",role="comping",dynamic=.48,accent=.4,harmony_label="G7",ensemble_role="support",tags=frozenset({"comping"})),
                StructuralPerformanceEvent("e5",2,.5,unpitched_token="ride",instrument="drums",role="comping",dynamic=.55,accent=.8,ensemble_role="response",tags=frozenset({"comping"})),
                StructuralPerformanceEvent("e6",2.5,.5,60,instrument="piano",role="solo",dynamic=.5,accent=.5,harmony_label="Dm7",phrase_id="p2",ensemble_role="foreground"),
                StructuralPerformanceEvent("e7",3,.5,62,instrument="piano",role="solo",dynamic=.58,accent=.7,harmony_label="Dm7",phrase_id="p2",ensemble_role="foreground"),
                StructuralPerformanceEvent("e8",3.5,.5,63,instrument="piano",role="solo",dynamic=.62,accent=.6,harmony_label="G7",phrase_id="p2",ensemble_role="foreground"),
            ),
        )


def item(training=True):
    return CorpusItem(
        item_id="audio.test",
        kind=CorpusKind.MUSICAL_INTELLIGENCE,
        media_type="audio/mpeg",
        title="test",
        local_relpath="audio/test.mp3",
        access=CorpusAccess.LOCAL_PRIVATE,
        uses=frozenset({CorpusUse.TRAINING,CorpusUse.RESEARCH}),
        rights=RightsProfile(training_permission=True if training else None,research_permission=True),
    )


def test_one_audio_analysis_fans_out_to_many_learning_domains():
    result=convert_audio_to_learning_data(item(),Path("x.mp3"),FakeAnalyzer())
    domains={x.domain for x in result.artifacts}
    assert LearningDomain.MOTIF in domains
    assert LearningDomain.SOLO_PHRASE in domains
    assert LearningDomain.COMPING in domains
    assert LearningDomain.HARMONY_VOICE_LEADING in domains
    assert LearningDomain.RHYTHM_MICROTIMING in domains
    assert LearningDomain.ENSEMBLE_INTERACTION in domains
    assert LearningDomain.EXPRESSION in domains
    assert LearningDomain.FORM_TENSION in domains
    assert result.disposition is LearningDisposition.TRAINING_ELIGIBLE
    assert result.training_artifacts


def test_unknown_training_rights_still_convert_but_do_not_enter_training_pool():
    result=convert_audio_to_learning_data(item(training=False),Path("x.mp3"),FakeAnalyzer())
    assert result.derived_artifacts
    assert result.training_artifacts==()
    assert result.disposition is LearningDisposition.DERIVED_ONLY


def test_learning_artifacts_do_not_store_absolute_audio_payload():
    result=convert_audio_to_learning_data(item(),Path("x.mp3"),FakeAnalyzer())
    assert result.artifacts
    assert all(not hasattr(x,"audio_bytes") for x in result.artifacts)
