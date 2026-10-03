from music_intelligence.reasoning.performance_convention import (
    JAZZ_JAM_SESSION_DEFAULT,
    PerformanceConvention,
    PerformanceConventionMode,
    default_performance_convention,
)


def test_jazz_defaults_to_jam_session_when_no_other_instruction_exists():
    policy=default_performance_convention("jazz")
    assert policy is JAZZ_JAM_SESSION_DEFAULT
    assert policy.shared_form
    assert policy.repeat_form_for_improvisation
    assert policy.single_foreground_default
    assert policy.accompaniment_yields_to_foreground
    assert policy.rhythm_section_preserves_form
    assert policy.head_in_when_written
    assert policy.head_out_when_written
    assert policy.trading_requires_explicit_cue


def test_common_jazz_substyles_resolve_to_same_jam_session_default():
    for genre in ("bebop","hard bop","post-bop","swing","modal jazz"):
        assert (
            default_performance_convention(genre).mode
            is PerformanceConventionMode.JAZZ_JAM_SESSION
        )


def test_explicit_arrangement_overrides_jazz_default():
    arranged=PerformanceConvention(
        genre_family="jazz",
        mode=PerformanceConventionMode.ARRANGED,
        shared_form=True,
        provenance=("user_explicit_arrangement",),
    )
    assert default_performance_convention("jazz",explicit=arranged) is arranged


def test_non_jazz_is_not_silently_given_jazz_jam_rules():
    policy=default_performance_convention("classical")
    assert policy.mode is PerformanceConventionMode.UNSPECIFIED
