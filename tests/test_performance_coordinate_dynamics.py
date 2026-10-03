from fractions import Fraction
import pytest
from music_intelligence.transcribe import MusicalCoordinate, PerceptualDynamics, DynamicChange

def test_musical_coordinate_validation():
    value = MusicalCoordinate(form="AABA", section="B", chorus=2, bar_in_section=5, beat=Fraction(3), subdivision=Fraction(2, 3), confidence=.8)
    value.validate()
    assert value.section == "B"
    assert value.subdivision == Fraction(2, 3)

def test_perceptual_dynamics_validation():
    value = PerceptualDynamics(dynamic_absolute_ordinal=.7, dynamic_relative_to_track=.6, dynamic_relative_to_section=.8, dynamic_relative_to_phrase=.9, dynamic_change=DynamicChange.CRESCENDO, dynamic_confidence=.75, dynamic_evidence=("brightness", "attack", "register", "density", "articulation", "sustain", "phrase-context"))
    value.validate()
    assert value.dynamic_relative_to_phrase == .9

def test_contract_rejects_invalid_normalized_values():
    with pytest.raises(ValueError):
        MusicalCoordinate(subdivision=Fraction(1)).validate()
    with pytest.raises(ValueError):
        PerceptualDynamics(dynamic_relative_to_section=1.2).validate()
