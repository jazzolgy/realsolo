from music_intelligence.reasoning.legend_style_core import CandidateEvent
from music_intelligence.reasoning.offline_performance_audit import audit_completed_phrase

def test_offline_audit_reports_but_does_not_rewrite():
    events=[CandidateEvent(71,2.0,tags=frozenset({"exposed_maj7_natural11"}))]
    before=tuple(events)
    findings=audit_completed_phrase(events)
    assert findings and findings[0].code=="maj7_natural11"
    assert tuple(events)==before
