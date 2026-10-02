from music_intelligence.reasoning.feasibility import FeasibilityAssessment
from music_intelligence.reasoning.solo_candidates import SoloCandidateSpec
from music_intelligence.reasoning.solo_expression import SoloExpressionIntent
from music_intelligence.reasoning.solo_realizer import SoloRealizerRegistry


class DummyRealizer:
    def realize(self, candidate, expression, context):
        return (candidate.pitch_class, expression.dynamic_energy, context)


def test_shared_feasibility_schema():
    x=FeasibilityAssessment(True,cost=.2,transition_cost=.1,physical_conflict=.0,confidence=.9)
    x.validate()


def test_solo_realizer_registry_does_not_know_instruments():
    r=SoloRealizerRegistry()
    r.register("dummy",DummyRealizer())
    out=r.realize("dummy",SoloCandidateSpec(0,.5),SoloExpressionIntent(dynamic_energy=.7),"ctx")
    assert out==(0,.7,"ctx")
