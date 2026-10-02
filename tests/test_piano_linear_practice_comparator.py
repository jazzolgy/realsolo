from music_intelligence.harmony.scale_linear_core import LinearRouteKind
from players.piano import (
    AbstractWrittenLineObservation,
    ContourClass,
    IntervalMotionClass,
    MotionSourceClass,
    TargetHorizonClass,
    compare_abstract_routes,
)


def observation():
    return AbstractWrittenLineObservation(
        observation_id="anthropology.fast_bebop.head",
        song_id="score.newreal1.anthropology",
        source_locator="NewReal1.pdf:p11",
        likely_routes=(
            LinearRouteKind.CHORDAL,
            LinearRouteKind.DIATONIC_PASSING,
            LinearRouteKind.CHROMATIC_PASSING,
            LinearRouteKind.APPROACH,
            LinearRouteKind.ENCLOSURE,
        ),
        structural_targets=("guide_tone","chord_tone","next_harmony_target"),
        interval_motion=IntervalMotionClass.SMALL_MIXED,
        motion_source=MotionSourceClass.MIXED,
        contour=ContourClass.MIXED,
        target_horizon=TargetHorizonClass.SHORT,
        section_role="head",
        rhythmic_density="high",
        confidence=.90,
        provenance=("vision:NewReal1:p11","manual-abstract-review"),
    )


def test_abstract_comparator_measures_route_family_recall():
    obs=observation()
    result=compare_abstract_routes(
        obs,
        (
            LinearRouteKind.CHORDAL,
            LinearRouteKind.DIATONIC_PASSING,
            LinearRouteKind.CHROMATIC_PASSING,
            LinearRouteKind.APPROACH,
        ),
        target_alignment=.9,
    )
    assert result.route_recall == .8
    assert result.target_alignment == .9
    assert any("enclosure" in note for note in result.notes)


def test_extra_route_ratio_tracks_candidate_only_families():
    obs=observation()
    result=compare_abstract_routes(
        obs,
        obs.likely_routes + (LinearRouteKind.SCALE_FRAGMENT,),
    )
    assert result.route_recall == 1.0
    assert result.extra_route_ratio > 0


def test_observation_schema_contains_no_literal_phrase_fields():
    obs=observation()
    forbidden={
        "pitches",
        "rhythm",
        "literal_phrase",
        "melody",
        "note_sequence",
        "future_notes",
    }
    assert not forbidden & set(obs.__dataclass_fields__)


def test_comparator_accepts_only_abstract_route_families():
    obs=observation()
    result=compare_abstract_routes(
        obs,
        (LinearRouteKind.CHORDAL,LinearRouteKind.APPROACH),
    )
    assert all(isinstance(x,LinearRouteKind) for x in result.candidate_routes)
