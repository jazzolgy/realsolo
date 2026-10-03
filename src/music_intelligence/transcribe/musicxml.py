"""MusicXML 4.0 projection for ReadableScore.

MusicXML is an output adapter.  It is never used as the internal UMR or
notation-intent representation.
"""
from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from math import floor, lcm
from xml.etree import ElementTree as ET

from .engraving import BeamState, EngravingIntent, EngravingPlan, StemDirection
from .instrument_profiles import InstrumentProfile, resolve_instrument_profile
from .notation import NotatedAtomKind
from .rhythm import written_note_type_and_dots
from .score import (
    ReadableScore,
    ScoreEvent,
    ScoreKeySignature,
    ScorePart,
    ScoreSpanner,
    ScoreTextDirection,
)


def _divisions_for_score(score: ReadableScore) -> int:
    denominators = [1]
    for part in score.parts:
        for event in part.events:
            denominators.extend(
                (event.span.onset.denominator, event.span.duration.denominator)
            )
    return max(1, lcm(*denominators))


def _append_pitch(note: ET.Element, event: ScoreEvent) -> None:
    if event.written_pitch is not None:
        pitch = ET.SubElement(note, "pitch")
        ET.SubElement(pitch, "step").text = event.written_pitch.step
        if event.written_pitch.alter:
            ET.SubElement(pitch, "alter").text = str(event.written_pitch.alter)
        ET.SubElement(pitch, "octave").text = str(event.written_pitch.octave)
    elif event.unpitched is not None:
        unpitched = ET.SubElement(note, "unpitched")
        ET.SubElement(unpitched, "display-step").text = "C"
        ET.SubElement(unpitched, "display-octave").text = "5"


def _append_notations(note: ET.Element, event: ScoreEvent) -> None:
    need_notations = (
        event.tie_from_previous
        or event.tie_to_next
        or event.articulations
        or event.markings
    )
    if not need_notations:
        return
    notations = ET.SubElement(note, "notations")
    if event.tie_from_previous:
        ET.SubElement(notations, "tied", {"type": "stop"})
    if event.tie_to_next:
        ET.SubElement(notations, "tied", {"type": "start"})
    if event.articulations:
        arts = ET.SubElement(notations, "articulations")
        supported = {
            "accent",
            "staccato",
            "tenuto",
            "strong-accent",
            "detached-legato",
        }
        for articulation in event.articulations:
            if articulation in supported:
                ET.SubElement(arts, articulation)
            else:
                ET.SubElement(arts, "other-articulation").text = articulation
    for marking in event.markings:
        ET.SubElement(notations, "other-notation").text = marking


def _append_dynamic_direction(
    measure: ET.Element,
    event: ScoreEvent,
    *,
    staff_number: int,
) -> None:
    if event.dynamic_marking is None:
        return
    direction = ET.SubElement(measure, "direction", {"placement": "below"})
    direction_type = ET.SubElement(direction, "direction-type")
    dynamics = ET.SubElement(direction_type, "dynamics")
    ET.SubElement(dynamics, event.dynamic_marking)
    ET.SubElement(direction, "staff").text = str(staff_number)




def _append_text_direction(
    measure: ET.Element,
    direction_spec: ScoreTextDirection,
    *,
    measure_start: Fraction,
    divisions: int,
) -> None:
    direction = ET.SubElement(
        measure,
        "direction",
        {"placement": direction_spec.placement},
    )
    direction_type = ET.SubElement(direction, "direction-type")
    ET.SubElement(direction_type, "words").text = direction_spec.text
    offset = direction_spec.onset - measure_start
    if offset > 0:
        ET.SubElement(direction, "offset").text = str(int(offset * divisions))


def _append_wedge_direction(
    measure: ET.Element,
    spanner: ScoreSpanner,
    *,
    staff_number: int,
    number: int,
    stop: bool = False,
) -> None:
    direction = ET.SubElement(measure, "direction", {"placement": spanner.placement})
    direction_type = ET.SubElement(direction, "direction-type")
    wedge_type = "stop" if stop else spanner.kind.value
    ET.SubElement(
        direction_type,
        "wedge",
        {"type": wedge_type, "number": str(number)},
    )
    ET.SubElement(direction, "staff").text = str(staff_number)


def _spanner_events_for_part(
    score: ReadableScore,
    part: ScorePart,
) -> dict[str, list[tuple[ScoreSpanner, int, bool]]]:
    by_event: dict[str, list[tuple[ScoreSpanner, int, bool]]] = defaultdict(list)
    part_spanners = sorted(
        (s for s in score.spanners if s.part_id == part.part_id),
        key=lambda s: s.spanner_id,
    )
    for number, spanner in enumerate(part_spanners, start=1):
        by_event[spanner.start_event_id].append((spanner, number, False))
        by_event[spanner.end_event_id].append((spanner, number, True))
    return by_event


def _append_note(
    measure: ET.Element,
    event: ScoreEvent,
    *,
    divisions: int,
    staff_number: int,
    engraving: EngravingIntent | None = None,
    chord_member: bool = False,
) -> None:
    note = ET.SubElement(measure, "note")
    if chord_member:
        ET.SubElement(note, "chord")
    if event.grace_kind is not None:
        grace_attrs = {"slash": "yes"} if event.grace_kind.value == "acciaccatura" else {}
        ET.SubElement(note, "grace", grace_attrs)
    if event.kind is NotatedAtomKind.REST:
        ET.SubElement(note, "rest")
    else:
        _append_pitch(note, event)

    if event.grace_kind is None:
        duration = int(event.span.duration * divisions)
        ET.SubElement(note, "duration").text = str(duration)
        note_type, dots = written_note_type_and_dots(
            event.span.duration,
            tuplet=event.tuplet,
        )
        if note_type is not None:
            ET.SubElement(note, "type").text = note_type
            for _ in range(dots):
                ET.SubElement(note, "dot")
    ET.SubElement(note, "voice").text = event.voice_id
    ET.SubElement(note, "staff").text = str(staff_number)

    if engraving is not None:
        if engraving.stem_direction is not StemDirection.AUTO:
            ET.SubElement(note, "stem").text = engraving.stem_direction.value
        if engraving.beam_state is not BeamState.NONE:
            ET.SubElement(note, "beam", {"number": "1"}).text = engraving.beam_state.value
        if engraving.secondary_beam_state is not BeamState.NONE:
            ET.SubElement(note, "beam", {"number": "2"}).text = (
                engraving.secondary_beam_state.value
            )

    if event.tie_from_previous:
        ET.SubElement(note, "tie", {"type": "stop"})
    if event.tie_to_next:
        ET.SubElement(note, "tie", {"type": "start"})

    if event.tuplet is not None:
        tm = ET.SubElement(note, "time-modification")
        ET.SubElement(tm, "actual-notes").text = str(event.tuplet.actual)
        ET.SubElement(tm, "normal-notes").text = str(event.tuplet.normal)

    _append_notations(note, event)


def _profile_for_part(part: ScorePart) -> InstrumentProfile | None:
    if part.profile_id is not None:
        profile = resolve_instrument_profile(part.profile_id)
        if profile is None:
            raise ValueError(f"unknown instrument profile: {part.profile_id}")
        return profile
    return resolve_instrument_profile(part.instrument)


def _append_profile_attributes(
    attrs: ET.Element,
    part: ScorePart,
    *,
    concert_key: ScoreKeySignature,
) -> None:
    profile = _profile_for_part(part)
    fifth_shift = 0
    if profile is not None and profile.transposition.diatonic_steps is not None:
        chromatic = (-profile.transposition.chromatic_semitones) % 12
        diatonic = (-profile.transposition.diatonic_steps) % 7
        fifth_shift = 7 * chromatic - 12 * diatonic
    fifths = concert_key.fifths + fifth_shift
    while fifths > 7:
        fifths -= 12
    while fifths < -7:
        fifths += 12
    key = ET.SubElement(attrs, "key")
    ET.SubElement(key, "fifths").text = str(fifths)
    ET.SubElement(key, "mode").text = concert_key.mode
    if profile is None:
        return
    if profile.staff_count != len(part.staff_ids):
        raise ValueError(
            f"instrument profile {profile.profile_id} expects "
            f"{profile.staff_count} staff/staves, got {len(part.staff_ids)}"
        )

    for index, clef_spec in enumerate(profile.clefs, start=1):
        clef_attrs = {"number": str(index)} if len(profile.clefs) > 1 else {}
        clef = ET.SubElement(attrs, "clef", clef_attrs)
        ET.SubElement(clef, "sign").text = clef_spec.sign
        if clef_spec.sign != "percussion":
            ET.SubElement(clef, "line").text = str(clef_spec.line)
        if clef_spec.octave_change:
            ET.SubElement(clef, "clef-octave-change").text = str(
                clef_spec.octave_change
            )

    transposition = profile.transposition
    if (
        transposition.chromatic_semitones
        or transposition.diatonic_steps is not None
        or transposition.octave_change
    ):
        transpose = ET.SubElement(attrs, "transpose")
        if transposition.diatonic_steps is not None:
            ET.SubElement(transpose, "diatonic").text = str(
                transposition.diatonic_steps
            )
        ET.SubElement(transpose, "chromatic").text = str(
            transposition.chromatic_semitones
        )
        if transposition.octave_change:
            ET.SubElement(transpose, "octave-change").text = str(
                transposition.octave_change
            )


def _dynamic_event_ids_to_emit(
    score: ReadableScore,
    part: ScorePart,
    engraving_plan: EngravingPlan | None,
) -> set[str]:
    """Choose only initial/changed dynamics for each rendered staff.

    Score events retain their performed dynamic projection.  This function only
    controls notation output so repeated identical markings do not clutter the
    readable score.
    """

    ordered = sorted(
        part.events,
        key=lambda event: (
            event.span.onset,
            event.staff_id,
            event.voice_id,
            event.event_id,
        ),
    )
    last_by_staff: dict[str, str] = {}
    emitted: set[str] = set()
    seen_at_onset: set[tuple[str, Fraction, str]] = set()

    events_by_id = {event.event_id: event for event in part.events}
    hairpin_interior_ids: set[str] = set()
    hairpin_endpoint_ids: set[str] = set()
    for spanner in score.spanners:
        if spanner.part_id != part.part_id:
            continue
        if spanner.kind.value not in {"crescendo", "diminuendo"}:
            continue
        start = events_by_id.get(spanner.start_event_id)
        end = events_by_id.get(spanner.end_event_id)
        if start is None or end is None:
            continue
        hairpin_endpoint_ids.update({start.event_id, end.event_id})
        for event in part.events:
            if start.span.onset < event.span.onset < end.span.onset:
                hairpin_interior_ids.add(event.event_id)

    for event in ordered:
        marking = event.dynamic_marking
        if marking is None:
            continue
        if (
            event.event_id in hairpin_interior_ids
            and event.event_id not in hairpin_endpoint_ids
        ):
            continue

        engraving = (
            engraving_plan.for_event(event.event_id)
            if engraving_plan is not None
            else None
        )
        rendered_staff = (
            engraving.cross_staff_target
            if engraving is not None and engraving.cross_staff_target is not None
            else event.staff_id
        )

        onset_key = (rendered_staff, event.span.onset, marking)
        if onset_key in seen_at_onset:
            continue
        seen_at_onset.add(onset_key)

        if last_by_staff.get(rendered_staff) == marking:
            continue

        emitted.add(event.event_id)
        last_by_staff[rendered_staff] = marking

    return emitted


def _part_measures(
    part: ScorePart,
    *,
    bar_length: Fraction,
) -> dict[int, list[ScoreEvent]]:
    by_measure: dict[int, list[ScoreEvent]] = defaultdict(list)
    for event in part.events:
        index = floor(event.span.onset / bar_length)
        if event.span.offset > (index + 1) * bar_length:
            raise ValueError(
                "score event crosses measure boundary; split with ties before MusicXML export"
            )
        by_measure[index].append(event)
    return by_measure


def score_to_musicxml(
    score: ReadableScore,
    engraving_plan: EngravingPlan | None = None,
) -> str:
    score.validate()
    if engraving_plan is not None:
        engraving_plan.validate(score)
    divisions = _divisions_for_score(score)
    bar_length = Fraction(
        score.meter_numerator * 4,
        score.meter_denominator,
    )
    bar_duration = int(bar_length * divisions)

    root = ET.Element("score-partwise", {"version": "4.0"})
    work = ET.SubElement(root, "work")
    ET.SubElement(work, "work-title").text = score.title

    part_list = ET.SubElement(root, "part-list")
    for part in score.parts:
        score_part = ET.SubElement(part_list, "score-part", {"id": part.part_id})
        ET.SubElement(score_part, "part-name").text = part.name

    global_directions_by_measure: dict[int, list[ScoreTextDirection]] = defaultdict(list)
    for direction in score.directions:
        measure_index = floor(direction.onset / bar_length)
        global_directions_by_measure[measure_index].append(direction)

    for part_index, part in enumerate(score.parts):
        part_el = ET.SubElement(root, "part", {"id": part.part_id})
        measures = _part_measures(part, bar_length=bar_length)
        max_measure = max(measures, default=0)
        staff_numbers = {sid: i + 1 for i, sid in enumerate(part.staff_ids)}
        dynamic_event_ids = _dynamic_event_ids_to_emit(score, part, engraving_plan)
        spanner_events = _spanner_events_for_part(score, part)

        for measure_index in range(max_measure + 1):
            measure = ET.SubElement(
                part_el,
                "measure",
                {"number": str(measure_index + 1)},
            )
            if measure_index == 0:
                attrs = ET.SubElement(measure, "attributes")
                ET.SubElement(attrs, "divisions").text = str(divisions)
                time = ET.SubElement(attrs, "time")
                ET.SubElement(time, "beats").text = str(score.meter_numerator)
                ET.SubElement(time, "beat-type").text = str(score.meter_denominator)
                if len(part.staff_ids) > 1:
                    ET.SubElement(attrs, "staves").text = str(len(part.staff_ids))
                _append_profile_attributes(attrs, part, concert_key=score.key_signature)

            if part_index == 0:
                measure_start = bar_length * measure_index
                for direction_spec in global_directions_by_measure.get(
                    measure_index,
                    (),
                ):
                    _append_text_direction(
                        measure,
                        direction_spec,
                        measure_start=measure_start,
                        divisions=divisions,
                    )

            events = measures.get(measure_index, [])
            groups: dict[tuple[str, str], list[ScoreEvent]] = defaultdict(list)
            for event in events:
                groups[(event.staff_id, event.voice_id)].append(event)

            first_group = True
            previous_group_cursor = bar_length * measure_index
            for (staff_id, voice_id), voice_events in sorted(groups.items()):
                voice_events.sort(key=lambda e: (e.span.onset, e.event_id))
                measure_start = bar_length * measure_index
                cursor = measure_start

                if not first_group:
                    rewind = previous_group_cursor - measure_start
                    if rewind > 0:
                        backup = ET.SubElement(measure, "backup")
                        ET.SubElement(backup, "duration").text = str(
                            int(rewind * divisions)
                        )
                first_group = False

                emitted_simultaneity_groups: set[str] = set()
                for event in voice_events:
                    if event.span.onset > cursor:
                        forward = ET.SubElement(measure, "forward")
                        ET.SubElement(forward, "duration").text = str(
                            int((event.span.onset - cursor) * divisions)
                        )
                    engraving = (
                        engraving_plan.for_event(event.event_id)
                        if engraving_plan is not None
                        else None
                    )
                    rendered_staff_id = (
                        engraving.cross_staff_target
                        if engraving is not None and engraving.cross_staff_target is not None
                        else staff_id
                    )
                    if rendered_staff_id not in staff_numbers:
                        raise ValueError(
                            f"engraving cross_staff_target is not in part: {rendered_staff_id}"
                        )
                    chord_member = (
                        event.simultaneity_group_id is not None
                        and event.simultaneity_group_id in emitted_simultaneity_groups
                    )
                    if not chord_member:
                        for spanner, number, stop in spanner_events.get(
                            event.event_id,
                            (),
                        ):
                            _append_wedge_direction(
                                measure,
                                spanner,
                                staff_number=staff_numbers[rendered_staff_id],
                                number=number,
                                stop=stop,
                            )
                    if not chord_member and event.event_id in dynamic_event_ids:
                        _append_dynamic_direction(
                            measure,
                            event,
                            staff_number=staff_numbers[rendered_staff_id],
                        )
                    _append_note(
                        measure,
                        event,
                        divisions=divisions,
                        staff_number=staff_numbers[rendered_staff_id],
                        engraving=engraving,
                        chord_member=chord_member,
                    )
                    if event.simultaneity_group_id is not None:
                        emitted_simultaneity_groups.add(event.simultaneity_group_id)
                    if not chord_member:
                        cursor = event.span.offset
                previous_group_cursor = cursor

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)
