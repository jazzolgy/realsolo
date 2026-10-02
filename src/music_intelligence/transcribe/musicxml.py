"""MusicXML 4.0 projection for ReadableScore.

MusicXML is an output adapter.  It is never used as the internal UMR or
notation-intent representation.
"""
from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from math import floor, lcm
from xml.etree import ElementTree as ET

from .notation import NotatedAtomKind
from .score import ReadableScore, ScoreEvent, ScorePart


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


def _append_note(
    measure: ET.Element,
    event: ScoreEvent,
    *,
    divisions: int,
    staff_number: int,
) -> None:
    note = ET.SubElement(measure, "note")
    if event.kind is NotatedAtomKind.REST:
        ET.SubElement(note, "rest")
    else:
        _append_pitch(note, event)

    duration = int(event.span.duration * divisions)
    ET.SubElement(note, "duration").text = str(duration)
    ET.SubElement(note, "voice").text = event.voice_id
    ET.SubElement(note, "staff").text = str(staff_number)

    if event.tie_from_previous:
        ET.SubElement(note, "tie", {"type": "stop"})
    if event.tie_to_next:
        ET.SubElement(note, "tie", {"type": "start"})

    if event.tuplet is not None:
        tm = ET.SubElement(note, "time-modification")
        ET.SubElement(tm, "actual-notes").text = str(event.tuplet.actual)
        ET.SubElement(tm, "normal-notes").text = str(event.tuplet.normal)

    _append_notations(note, event)


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


def score_to_musicxml(score: ReadableScore) -> str:
    score.validate()
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

    for part in score.parts:
        part_el = ET.SubElement(root, "part", {"id": part.part_id})
        measures = _part_measures(part, bar_length=bar_length)
        max_measure = max(measures, default=0)
        staff_numbers = {sid: i + 1 for i, sid in enumerate(part.staff_ids)}

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

                for event in voice_events:
                    if event.span.onset > cursor:
                        forward = ET.SubElement(measure, "forward")
                        ET.SubElement(forward, "duration").text = str(
                            int((event.span.onset - cursor) * divisions)
                        )
                    _append_note(
                        measure,
                        event,
                        divisions=divisions,
                        staff_number=staff_numbers[staff_id],
                    )
                    cursor = event.span.offset
                previous_group_cursor = cursor

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)
