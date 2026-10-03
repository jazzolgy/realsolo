"""Shared performance-convention defaults.

Jazz performance defaults to ordinary jam-session coordination unless an
explicit session/arrangement instruction overrides it. This module encodes
cross-player convention only; it does not choose notes, voicings, drum hits, or
instrument-specific realization.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PerformanceConventionMode(str, Enum):
    UNSPECIFIED = "unspecified"
    JAZZ_JAM_SESSION = "jazz_jam_session"
    ARRANGED = "arranged"
    CUSTOM = "custom"


@dataclass(frozen=True)
class PerformanceConvention:
    genre_family: str = ""
    mode: PerformanceConventionMode = PerformanceConventionMode.UNSPECIFIED
    shared_form: bool = False
    repeat_form_for_improvisation: bool = False
    single_foreground_default: bool = False
    accompaniment_yields_to_foreground: bool = False
    rhythm_section_preserves_form: bool = False
    head_in_when_written: bool = False
    head_out_when_written: bool = False
    trading_requires_explicit_cue: bool = True
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.mode is PerformanceConventionMode.JAZZ_JAM_SESSION:
            if self.genre_family.strip().lower() != "jazz":
                raise ValueError("jazz jam-session convention requires genre_family='jazz'")


JAZZ_JAM_SESSION_DEFAULT = PerformanceConvention(
    genre_family="jazz",
    mode=PerformanceConventionMode.JAZZ_JAM_SESSION,
    shared_form=True,
    repeat_form_for_improvisation=True,
    single_foreground_default=True,
    accompaniment_yields_to_foreground=True,
    rhythm_section_preserves_form=True,
    head_in_when_written=True,
    head_out_when_written=True,
    trading_requires_explicit_cue=True,
    provenance=("shared_default:jazz_jam_session",),
)


def default_performance_convention(
    genre_family: str,
    *,
    explicit: PerformanceConvention | None = None,
) -> PerformanceConvention:
    """Resolve a performance convention without overriding explicit direction.

    Precedence:
      explicit user/session/arrangement instruction
      > written score/chart instruction
      > genre performance convention
      > style/legend soft priors
      > player realization

    This resolver implements only the genre-default step. Callers pass an
    explicit convention when a higher-priority instruction is present.
    """

    if explicit is not None:
        explicit.validate()
        return explicit

    genre=genre_family.strip().lower().replace("-","_").replace(" ","_")
    if genre in {
        "jazz",
        "bebop",
        "hard_bop",
        "post_bop",
        "swing",
        "modal_jazz",
    }:
        return JAZZ_JAM_SESSION_DEFAULT

    return PerformanceConvention(
        genre_family=genre_family.strip().lower(),
        mode=PerformanceConventionMode.UNSPECIFIED,
        provenance=("shared_default:unspecified",),
    )
