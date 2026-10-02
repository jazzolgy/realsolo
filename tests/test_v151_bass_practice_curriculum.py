from music_intelligence.bass.practice_curriculum import (
    BassPracticeLevel,
    bebop_walking_practice_curriculum,
    curriculum_feature_weights,
)


def test_curriculum_moves_from_foundation_to_variation():
    items = bebop_walking_practice_curriculum()
    assert items[0].level is BassPracticeLevel.ROOT_ORIENTATION
    assert any(x.level is BassPracticeLevel.HALF_TIME_APPROACH for x in items)
    assert any(x.level is BassPracticeLevel.ANTI_TEMPLATE for x in items)
    assert items[-1].level is BassPracticeLevel.RHYTHMIC_PUNCTUATION


def test_two_feel_practice_explicitly_restrains_third_seventh_overuse():
    item = next(
        x for x in bebop_walking_practice_curriculum()
        if x.level is BassPracticeLevel.HALF_TIME_APPROACH
    )
    assert "root_fifth_center" in item.required_behaviors
    assert "frequent_third_seventh_on_second_pulse" in item.avoid_behaviors


def test_walking_practice_rejects_one_bar_formula():
    item = next(
        x for x in bebop_walking_practice_curriculum()
        if x.level is BassPracticeLevel.WALKING_CONNECTION
    )
    assert "approach_on_every_bar" in item.avoid_behaviors
    assert "root_chordtone_chordtone_approach_template" in item.avoid_behaviors


def test_anti_template_level_weights_variety_strongly():
    weights = curriculum_feature_weights(BassPracticeLevel.ANTI_TEMPLATE)
    assert weights["role_pattern_variety"] > weights["harmonic_orientation"]
    assert weights["contour_variety"] >= 1.0
