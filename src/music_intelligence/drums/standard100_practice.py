"""Practice the bebop drummer across the private iReal standard100 corpus.

Raw/private charts remain under REALSOLO_CORPUS_ROOT.  This module stores no
copyrighted chart content in the public repository.  It reads source metadata
conservatively, runs deterministic drummer exercises, and writes derived
performance summaries under the private corpus root.

When a chart field is absent, the loader records it as unknown rather than
inventing musical facts.  Synthetic exercise overlays are explicitly marked.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
import json
from pathlib import Path
from typing import Any, Iterable

from music_intelligence.corpus import corpus_root_from_env
from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    InteractionKind,
    PlayerActionIntent,
    PlayerPresence,
    PlayerRole,
    TransportState,
    update_player_intent,
)

from .bebop import BebopPhraseMemory, SoloistEnergyProjection
from .bebop_runtime import (
    BebopRuntimeProjection,
    perform_one_bebop_gesture,
)
from .comping_phrase import (
    CompPhraseAction,
    SnarePhraseMemory,
    normalized_bar_phase,
    record_committed_snare_event,
)
from .model import DrummerRuntimeContext, DrummerSoftPlan, DrumVoice
from .online_drummer import DrummerPerformanceMemory
from .ride_continuity import (
    RideContinuityMemory,
    RidePhase,
    RideSurfaceAction,
    classify_ride_phase,
    update_ride_memory,
)
from .timing import tempo_conditioned_swing_prior


STANDARD100_RELPATH = Path("symbolic/irealb_v1_0/standard100")
DERIVED_RELPATH = Path("derived/drums/standard100")


@dataclass(frozen=True)
class ChartSection:
    label: str
    bars: int

    def validate(self) -> None:
        if self.bars <= 0:
            raise ValueError("section bars must be positive")


@dataclass(frozen=True)
class StandardChart:
    source_path: str
    title: str
    meter_numerator: int | None = None
    meter_denominator: int | None = None
    tempo_bpm: float | None = None
    bar_count: int | None = None
    sections: tuple[ChartSection, ...] = ()
    parse_notes: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.source_path or not self.title:
            raise ValueError("source_path and title are required")
        if self.meter_numerator is not None and self.meter_numerator <= 0:
            raise ValueError("meter numerator must be positive")
        if self.meter_denominator is not None and self.meter_denominator <= 0:
            raise ValueError("meter denominator must be positive")
        if self.tempo_bpm is not None and self.tempo_bpm <= 0:
            raise ValueError("tempo must be positive")
        if self.bar_count is not None and self.bar_count <= 0:
            raise ValueError("bar_count must be positive")
        for section in self.sections:
            section.validate()


@dataclass(frozen=True)
class SongPracticeResult:
    title: str
    source_path: str
    practiced: bool
    bars_practiced: int
    decisions: int
    ride_quarter_actions: int
    ride_skip_actions: int
    ride_skip_omissions: int
    intentional_non_responses: int
    snare_phrase_actions: int
    retrospective_motif_hits: int
    bass_floor_events: int
    build_states: int
    coast_states: int
    come_down_states: int
    handoff_states: int
    parse_notes: tuple[str, ...]
    exercise_notes: tuple[str, ...]


@dataclass(frozen=True)
class Standard100PracticeReport:
    corpus_path: str
    files_discovered: int
    charts_loaded: int
    songs_practiced: int
    total_bars_practiced: int
    total_decisions: int
    results: tuple[SongPracticeResult, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


def standard100_root(root: str | Path | None = None) -> Path:
    base = Path(root).expanduser().resolve() if root is not None else corpus_root_from_env()
    path = base / STANDARD100_RELPATH
    if not path.exists():
        raise FileNotFoundError(f"standard100 corpus not found: {path}")
    if not path.is_dir():
        raise NotADirectoryError(path)
    return path


def discover_standard100_files(root: str | Path | None = None) -> tuple[Path, ...]:
    path = standard100_root(root)
    allowed = {".json", ".jsonl", ".csv", ".txt", ".ireal", ".irealb"}
    files = tuple(sorted(
        p for p in path.rglob("*")
        if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in allowed
    ))
    return files


def _first(mapping: dict[str, Any], names: Iterable[str]) -> Any:
    lower = {str(k).lower(): v for k, v in mapping.items()}
    for name in names:
        if name.lower() in lower:
            return lower[name.lower()]
    return None


def _parse_meter(value: Any) -> tuple[int | None, int | None]:
    if value is None:
        return None, None
    if isinstance(value, str) and "/" in value:
        a, b = value.split("/", 1)
        try:
            return int(a), int(b)
        except ValueError:
            return None, None
    if isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            return int(value[0]), int(value[1])
        except (TypeError, ValueError):
            return None, None
    return None, None


def _section_from_mapping(value: Any) -> tuple[ChartSection, ...]:
    if not isinstance(value, list):
        return ()
    out: list[ChartSection] = []
    for index, entry in enumerate(value):
        if not isinstance(entry, dict):
            continue
        label = _first(entry, ("label", "name", "section", "mark")) or f"section_{index + 1}"
        bars = _first(entry, ("bars", "bar_count", "measures", "measure_count"))
        if isinstance(bars, list):
            bars = len(bars)
        try:
            bars_i = int(bars)
        except (TypeError, ValueError):
            continue
        if bars_i > 0:
            out.append(ChartSection(str(label), bars_i))
    return tuple(out)


def _chart_from_mapping(data: dict[str, Any], source: Path) -> StandardChart:
    notes: list[str] = []
    title = _first(data, ("title", "name", "song", "song_title", "tune"))
    if not title:
        title = source.stem
        notes.append("title_from_filename")

    meter = _first(data, ("meter", "time_signature", "timesig", "time"))
    num, den = _parse_meter(meter)
    if num is None:
        n = _first(data, ("meter_numerator", "numerator", "beats_per_bar"))
        d = _first(data, ("meter_denominator", "denominator", "beat_unit"))
        try:
            num = int(n) if n is not None else None
            den = int(d) if d is not None else None
        except (TypeError, ValueError):
            num = den = None

    tempo = _first(data, ("tempo", "tempo_bpm", "bpm"))
    try:
        tempo_f = float(tempo) if tempo is not None else None
    except (TypeError, ValueError):
        tempo_f = None
        notes.append("unparsed_tempo")

    sections = _section_from_mapping(_first(data, ("sections", "form_sections", "parts")))

    bars_value = _first(data, ("bar_count", "bars", "measure_count", "measures"))
    bar_count: int | None = None
    if isinstance(bars_value, list):
        bar_count = len(bars_value)
    elif isinstance(bars_value, int):
        bar_count = bars_value
    elif isinstance(bars_value, str) and bars_value.isdigit():
        bar_count = int(bars_value)
    if bar_count is None and sections:
        bar_count = sum(x.bars for x in sections)

    if bar_count is None:
        notes.append("bar_count_unknown")
    if num is None or den is None:
        notes.append("meter_unknown")
    if tempo_f is None:
        notes.append("tempo_unknown")

    chart = StandardChart(
        source_path=str(source),
        title=str(title),
        meter_numerator=num,
        meter_denominator=den,
        tempo_bpm=tempo_f,
        bar_count=bar_count,
        sections=sections,
        parse_notes=tuple(notes),
    )
    chart.validate()
    return chart


def load_standard_chart(path: Path) -> StandardChart:
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            if len(data) != 1 or not isinstance(data[0], dict):
                raise ValueError(f"JSON file is not one chart mapping: {path}")
            data = data[0]
        if not isinstance(data, dict):
            raise ValueError(f"JSON chart must be an object: {path}")
        return _chart_from_mapping(data, path)

    if suffix == ".jsonl":
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if len(rows) != 1 or not isinstance(rows[0], dict):
            raise ValueError(f"JSONL chart file must contain one object: {path}")
        return _chart_from_mapping(rows[0], path)

    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != 1:
            raise ValueError(f"CSV chart file must contain one data row: {path}")
        return _chart_from_mapping(dict(rows[0]), path)

    # Plain iReal/text formats are not guessed. We preserve only filename title
    # until a source-specific parser is verified against the actual corpus.
    return StandardChart(
        source_path=str(path),
        title=path.stem,
        parse_notes=("opaque_text_format_not_interpreted", "bar_count_unknown", "meter_unknown", "tempo_unknown"),
    )


def load_standard100(root: str | Path | None = None) -> tuple[StandardChart, ...]:
    charts: list[StandardChart] = []
    for path in discover_standard100_files(root):
        try:
            charts.append(load_standard_chart(path))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            # A malformed/aggregate file must not be silently converted to a
            # fictitious tune. It simply does not enter practice.
            continue
    return tuple(charts)


def _section_end_bars(chart: StandardChart) -> frozenset[int]:
    if not chart.sections:
        return frozenset()
    total = 0
    ends: set[int] = set()
    for section in chart.sections:
        total += section.bars
        ends.add(total - 1)
    return frozenset(ends)


def _exercise_state(pass_index: int, bar: int, bars: int) -> SoloistEnergyProjection:
    """Deterministic training overlay, explicitly not chart metadata."""
    phase = bar / max(1, bars - 1)
    mode = pass_index % 4
    if mode == 0:
        # Baseline conversational support.
        return SoloistEnergyProjection(
            activity=0.45 + 0.15 * phase,
            current_energy=0.45 + 0.20 * phase,
            energy_slope=0.08,
            phrase_terminal_probability=0.8 if phase > 0.92 else 0.1,
        )
    if mode == 1:
        # Rising soloist: tests BUILD vs COAST according to drummer history.
        return SoloistEnergyProjection(
            activity=min(0.95, 0.45 + 0.5 * phase),
            current_energy=min(0.95, 0.45 + 0.5 * phase),
            energy_slope=0.34,
            phrase_terminal_probability=0.1,
        )
    if mode == 2:
        # Post-climax release.
        return SoloistEnergyProjection(
            activity=max(0.35, 0.9 - 0.45 * phase),
            current_energy=max(0.35, 0.9 - 0.5 * phase),
            energy_slope=-0.28,
            phrase_terminal_probability=0.15,
            climax_probability=0.86,
        )
    # Dense soloist with openings; tests intentional non-response.
    return SoloistEnergyProjection(
        activity=0.88 if bar % 4 < 3 else 0.3,
        current_energy=0.72,
        energy_slope=0.05,
        phrase_terminal_probability=0.76 if bar % 4 == 3 else 0.1,
    )


def _walking_bass_state(
    *,
    bar: int,
    tempo: float,
    meter_numerator: int,
    form_position: float,
    boundary: bool,
) -> EnsembleState:
    state = EnsembleState(
        transport=TransportState(
            beat=1.0,
            bar=bar,
            section="",
            tempo_bpm=tempo,
            meter_numerator=meter_numerator,
            meter_denominator=4,
            form_position=form_position,
        ),
        players=(
            PlayerPresence("bass", "acoustic_bass", PlayerRole.BASS),
            PlayerPresence("drums", "drums", PlayerRole.DRUMS),
            PlayerPresence("soloist", "melody", PlayerRole.SOLOIST),
        ),
    )
    tags = {"walking", "quarter_note_pulse"}
    interaction = InteractionKind.LOCK
    phrase_maturity = 0.9 if boundary else 0.4
    if boundary:
        tags.add("figure")
    return update_player_intent(
        state,
        PlayerActionIntent(
            "bass",
            interaction,
            density=0.78,
            energy=0.58,
            phrase_maturity=phrase_maturity,
            tags=frozenset(tags),
        ),
    )


def _ride_action_from_tags(tags: frozenset[str]) -> RideSurfaceAction | None:
    for action in RideSurfaceAction:
        if action.value in tags:
            return action
    return None


def _snare_action_from_tags(tags: frozenset[str]) -> CompPhraseAction | None:
    for action in CompPhraseAction:
        if action.value in tags:
            return action
    return None


def practice_chart(
    chart: StandardChart,
    *,
    passes: int = 4,
    default_tempo: float = 160.0,
) -> SongPracticeResult:
    """Run deterministic bebop accompaniment drills over one chart form."""
    chart.validate()
    if chart.bar_count is None:
        return SongPracticeResult(
            chart.title, chart.source_path, False, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, chart.parse_notes,
            ("not_practiced_without_source_bar_count",),
        )

    bars = chart.bar_count
    meter = chart.meter_numerator or 4
    tempo = chart.tempo_bpm or default_tempo
    synthetic_defaults: list[str] = []
    if chart.meter_numerator is None:
        synthetic_defaults.append("exercise_overlay_meter_4_4")
    if chart.tempo_bpm is None:
        synthetic_defaults.append(f"exercise_overlay_tempo_{default_tempo:g}")

    section_ends = _section_end_bars(chart)
    if not section_ends:
        synthetic_defaults.append("no_section_metadata_no_section_boundary_invented")

    perf = DrummerPerformanceMemory()
    ride_memory = RideContinuityMemory()
    snare_memory = SnarePhraseMemory()
    phrase_memory = BebopPhraseMemory()

    ride_quarters = ride_skips = ride_skip_omits = 0
    nonresponses = snare_actions = retro_hits = bass_floor = 0
    build = coast = come_down = handoff = 0
    decisions = 0

    plan = DrummerSoftPlan(
        style_tags=frozenset({"jazz", "bop"}),
        energy=0.55,
        comping_density=0.42,
    )

    for pass_index in range(passes):
        for bar in range(bars):
            form_position = bar / max(1, bars - 1)
            source_boundary = bar in section_ends or bar == bars - 1
            soloist = _exercise_state(pass_index, bar, bars)
            bass_state = _walking_bass_state(
                bar=bar,
                tempo=tempo,
                meter_numerator=meter,
                form_position=form_position,
                boundary=source_boundary,
            )

            # Current-time decisions only: quarters plus the tempo-conditioned
            # skip location inside each beat.
            prior = tempo_conditioned_swing_prior(tempo)
            positions: list[float] = []
            for beat in range(meter):
                positions.append(float(beat))
                skip = beat + prior.offbeat_fraction
                if skip < meter:
                    positions.append(skip)

            for position in positions:
                phrase_position = ((bar % 8) + position / meter) / 8.0
                # 8-bar phrase position is a labeled practice overlay only; it
                # never changes source form metadata.
                section_transition = source_boundary and position >= meter - 1
                context = DrummerRuntimeContext(
                    position_in_bar_beats=position,
                    tempo_bpm=tempo,
                    beats_per_bar=meter,
                    phrase_position=min(1.0, phrase_position),
                    ensemble_activity=0.55,
                    soloist_activity=soloist.activity,
                    energy_target=soloist.current_energy,
                    section_transition=section_transition,
                )
                projection = BebopRuntimeProjection.from_ensemble_state(
                    soloist=soloist,
                    phrase_memory=phrase_memory,
                    ensemble_state=bass_state,
                )
                projection = BebopRuntimeProjection(
                    soloist=projection.soloist,
                    phrase_memory=projection.phrase_memory,
                    bass=projection.bass,
                    ride_memory=ride_memory,
                    snare_memory=snare_memory,
                )
                chosen = perform_one_bebop_gesture(plan, context, projection, perf)
                decisions += 1

                state = chosen.interaction.state.value
                if state == "build":
                    build += 1
                elif state == "coast":
                    coast += 1
                elif state == "come_down":
                    come_down += 1
                elif state == "handoff":
                    handoff += 1

                tags = chosen.gesture.tags
                if "intentional_non_response" in tags:
                    nonresponses += 1
                if "bass_floor_support" in tags:
                    bass_floor += 1

                phase = classify_ride_phase(context)
                ride_action = _ride_action_from_tags(tags)
                if ride_action is not None:
                    if phase is RidePhase.QUARTER:
                        ride_quarters += 1
                    elif phase is RidePhase.SKIP:
                        ride_skips += 1
                        if ride_action is RideSurfaceAction.OMIT_SKIP:
                            ride_skip_omits += 1
                    ride_memory = update_ride_memory(ride_memory, ride_action, phase)

                snare_action = _snare_action_from_tags(tags)
                if snare_action is not None:
                    if snare_action is not CompPhraseAction.LEAVE_SPACE:
                        snare_actions += 1
                        snare_hits = [h for h in chosen.gesture.hits if h.voice is DrumVoice.SNARE]
                        if snare_hits:
                            bar_phase = normalized_bar_phase(context)
                            accent = min(1.0, snare_hits[0].velocity / 100.0)
                            snare_memory = record_committed_snare_event(
                                snare_memory,
                                bar_index=pass_index * bars + bar,
                                phase=bar_phase,
                                accent=accent,
                            )
                            if snare_memory.motif is not None:
                                retro_hits = max(retro_hits, len(snare_memory.motif.onset_phases))

    return SongPracticeResult(
        title=chart.title,
        source_path=chart.source_path,
        practiced=True,
        bars_practiced=bars * passes,
        decisions=decisions,
        ride_quarter_actions=ride_quarters,
        ride_skip_actions=ride_skips,
        ride_skip_omissions=ride_skip_omits,
        intentional_non_responses=nonresponses,
        snare_phrase_actions=snare_actions,
        retrospective_motif_hits=retro_hits,
        bass_floor_events=bass_floor,
        build_states=build,
        coast_states=coast,
        come_down_states=come_down,
        handoff_states=handoff,
        parse_notes=chart.parse_notes,
        exercise_notes=tuple(synthetic_defaults + ["8_bar_phrase_position_is_training_overlay"]),
    )


def practice_standard100(
    root: str | Path | None = None,
    *,
    passes: int = 4,
    write_report: bool = True,
) -> Standard100PracticeReport:
    path = standard100_root(root)
    files = discover_standard100_files(root)
    charts = load_standard100(root)
    results = tuple(practice_chart(chart, passes=passes) for chart in charts)
    report = Standard100PracticeReport(
        corpus_path=str(path),
        files_discovered=len(files),
        charts_loaded=len(charts),
        songs_practiced=sum(1 for x in results if x.practiced),
        total_bars_practiced=sum(x.bars_practiced for x in results),
        total_decisions=sum(x.decisions for x in results),
        results=results,
    )
    if write_report:
        base = Path(root).expanduser().resolve() if root is not None else corpus_root_from_env()
        output = base / DERIVED_RELPATH
        output.mkdir(parents=True, exist_ok=True)
        (output / "practice_report.json").write_text(report.to_json(), encoding="utf-8")
    return report
