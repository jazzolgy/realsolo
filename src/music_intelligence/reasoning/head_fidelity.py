"""Shared written-head fidelity constraints.

A jazz head is an interpretation of the written melody, not a fresh solo over
the changes.  This module keeps the written note as the reference frame while
allowing bounded rhythmic and ornamental variation.

It is deliberately one-event causal: variants describe only the current written
melody event.  No future melody sequence is generated or stored.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .legend_style_core import CandidateEvent


class HeadFidelityMode(str, Enum):
    STRICT = "strict"
    NATURAL = "natural"
    LOOSE = "loose"


class HeadVariantKind(str, Enum):
    WRITTEN = "written"
    REPEAT = "repeat"
    SPLIT = "split"
    NEIGHBOR = "neighbor"
    PASSING = "passing"
    CHROMATIC_APPROACH = "chromatic_approach"


@dataclass(frozen=True)
class HeadFidelityContext:
    mode: HeadFidelityMode = HeadFidelityMode.NATURAL
    strong_beat: bool = False
    phrase_anchor: bool = False
    phrase_end: bool = False
    previous_written_pitch_midi: int | None = None
    next_written_pitch_midi: int | None = None
    harmonic_pitch_classes: frozenset[int] = frozenset()

    def validate(self) -> None:
        for pitch in (
            self.previous_written_pitch_midi,
            self.next_written_pitch_midi,
        ):
            if pitch is not None and not 0 <= pitch <= 127:
                raise ValueError("written melody pitch must be in MIDI range")
        if any(not 0 <= pc <= 11 for pc in self.harmonic_pitch_classes):
            raise ValueError("harmonic_pitch_classes must be within 0..11")


def _limits(ctx: HeadFidelityContext) -> tuple[int, float, float, float]:
    """Return pitch semitones, onset beats, min duration ratio, max ratio."""
    if ctx.mode is HeadFidelityMode.STRICT:
        return 0, .06, .85, 1.18
    if ctx.mode is HeadFidelityMode.NATURAL:
        return 2, .14, .48, 1.45
    return 4, .22, .34, 1.70


def _structurally_protected(ctx: HeadFidelityContext) -> bool:
    return ctx.strong_beat or ctx.phrase_anchor or ctx.phrase_end


def enforce_head_fidelity(
    written_event: CandidateEvent,
    proposed_event: CandidateEvent,
    context: HeadFidelityContext = HeadFidelityContext(),
) -> CandidateEvent:
    """Bound one proposed head event around its written source.

    Structural/strong-beat notes keep the exact written pitch.  Weak notes may
    deviate only locally.  Rhythm may breathe, split, repeat, or anticipate
    slightly, but it cannot be transformed beyond recognition.
    """
    context.validate()
    if written_event.duration_beats <= 0 or proposed_event.duration_beats <= 0:
        raise ValueError("head events must have positive duration")

    max_pitch_delta, max_onset, min_ratio, max_ratio = _limits(context)
    protected = _structurally_protected(context)

    pitch = proposed_event.pitch_midi
    if written_event.pitch_midi is None:
        pitch = None
    elif pitch is None:
        # A written melody note may not simply disappear in head mode.
        pitch = written_event.pitch_midi
    else:
        allowed_delta = 0 if protected else max_pitch_delta
        if abs(pitch - written_event.pitch_midi) > allowed_delta:
            pitch = written_event.pitch_midi

    base_duration = written_event.duration_beats
    duration = max(
        base_duration * min_ratio,
        min(base_duration * max_ratio, proposed_event.duration_beats),
    )
    onset = max(-max_onset, min(max_onset, proposed_event.onset_offset_beats))

    tags = set(proposed_event.tags) | {
        "head_melody",
        "head_fidelity_guard",
        f"head_fidelity:{context.mode.value}",
    }
    if pitch == written_event.pitch_midi:
        tags.add("written_pitch_preserved")
    if protected:
        tags.add("head_structural_pitch_locked")

    return replace(
        proposed_event,
        pitch_midi=pitch,
        duration_beats=duration,
        onset_offset_beats=onset,
        tags=frozenset(tags),
    )


def generate_head_candidate_variants(
    written_event: CandidateEvent,
    context: HeadFidelityContext = HeadFidelityContext(),
) -> tuple[CandidateEvent, ...]:
    """Generate conservative current-event alternatives around a written note.

    NATURAL (default):
    - exact written note is always present and preferred by downstream policy;
    - exact-pitch repeat/split variants may change rhythmic surface;
    - weak, non-anchor notes may use a nearby neighbor/passing tone;
    - strong beats / phrase anchors never change pitch.

    This function intentionally does not create a multi-note replacement phrase.
    """
    context.validate()
    written = enforce_head_fidelity(written_event, written_event, context)
    if written.pitch_midi is None:
        return (written,)

    out: list[CandidateEvent] = [
        replace(
            written,
            tags=frozenset(set(written.tags) | {
                "head_variant:written",
                "head_variant_preferred",
            }),
            source_family="head_written",
        )
    ]

    if context.mode is HeadFidelityMode.STRICT:
        return tuple(out)

    pitch = written.pitch_midi
    duration = written.duration_beats

    # Rhythmic interpretation without changing melodic identity.
    if duration >= .5:
        repeat_duration = max(.25, min(.5, duration * .55))
        out.append(enforce_head_fidelity(
            written_event,
            CandidateEvent(
                pitch,
                repeat_duration,
                onset_offset_beats=written.onset_offset_beats,
                tags=frozenset(set(written.tags) | {
                    "head_variant:repeat",
                    "head_rhythmic_repeat",
                }),
                source_family="head_repeat",
            ),
            context,
        ))
    if duration >= .75:
        split_duration = max(.25, duration * .5)
        out.append(enforce_head_fidelity(
            written_event,
            CandidateEvent(
                pitch,
                split_duration,
                onset_offset_beats=written.onset_offset_beats,
                tags=frozenset(set(written.tags) | {
                    "head_variant:split",
                    "head_rhythmic_split",
                }),
                source_family="head_split",
            ),
            context,
        ))

    if not _structurally_protected(context):
        # Nearby non-chord/connector color only.  Never replace a frame note by
        # a distant chord tone merely because the harmony permits it.
        for delta in (-1, 1):
            candidate_pitch = pitch + delta
            if not 0 <= candidate_pitch <= 127:
                continue
            tags = {
                "head_variant:neighbor",
                "head_ornament",
                "neighbor",
            }
            if (
                context.harmonic_pitch_classes
                and candidate_pitch % 12 not in context.harmonic_pitch_classes
            ):
                tags.add("non_chord_tone")
            out.append(enforce_head_fidelity(
                written_event,
                CandidateEvent(
                    candidate_pitch,
                    max(.25, min(duration, .5)),
                    onset_offset_beats=written.onset_offset_beats,
                    tags=frozenset(set(written.tags) | tags),
                    source_family="head_neighbor",
                ),
                context,
            ))

        # A diatonic-ish step may be useful when it follows the written contour.
        prev_pitch = context.previous_written_pitch_midi
        next_pitch = context.next_written_pitch_midi
        direction = 0
        if prev_pitch is not None and next_pitch is not None:
            if next_pitch > prev_pitch:
                direction = 1
            elif next_pitch < prev_pitch:
                direction = -1
        if direction:
            candidate_pitch = pitch + 2 * direction
            if 0 <= candidate_pitch <= 127:
                out.append(enforce_head_fidelity(
                    written_event,
                    CandidateEvent(
                        candidate_pitch,
                        max(.25, min(duration, .5)),
                        onset_offset_beats=written.onset_offset_beats,
                        tags=frozenset(set(written.tags) | {
                            "head_variant:passing",
                            "head_ornament",
                            "passing",
                        }),
                        source_family="head_passing",
                    ),
                    context,
                ))

    # Deterministic dedupe.
    unique: list[CandidateEvent] = []
    seen: set[tuple] = set()
    for event in out:
        key = (
            event.pitch_midi,
            round(event.duration_beats, 6),
            round(event.onset_offset_beats, 6),
            event.source_family,
            tuple(sorted(event.tags)),
        )
        if key not in seen:
            seen.add(key)
            unique.append(event)
    return tuple(unique)
