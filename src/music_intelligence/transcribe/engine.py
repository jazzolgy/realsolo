"""Stable facade for standalone and embedded notation applications.

Applications should prefer this facade over importing internal transcription
modules directly.  It provides a product boundary while the underlying
notation intelligence continues to evolve.
"""
from __future__ import annotations

from dataclasses import dataclass

from .allocation import StaffProfile
from .chord_chart import (
    ChordChart,
    ChordChartPosition,
    EnharmonicPolicy,
    chart_position,
)
from .chord_chart_quality import ChordChartAudit, audit_chord_chart
from .chord_chart_render import ChordChartRenderModel, build_chord_chart_render_model
from .chord_chart_viewport import (
    ChordChartViewport,
    ChordChartViewportConfig,
    build_chord_chart_viewport,
)
from .dynamics import (
    DynamicTrajectoryCandidate,
    infer_dynamic_trajectory,
    score_spanner_from_dynamic_trajectory,
)
from .engraving import EngravingPlan, EngravingProfile, build_default_engraving_plan
from .events import CommittedPerformanceEvent
from .instrument_profiles import (
    InstrumentProfile,
    TranspositionSpec,
    resolve_instrument_profile,
)
from .instrument_rules import InstrumentNotationDirective
from .musicxml import score_to_musicxml
from .projection import EventProjectionResult, project_pitched_event
from .quality import ScoreQualityReport, audit_score_for_performance
from .score import ReadableScore, ScoreEvent, ScoreSpanner
from .spelling import PitchSpellingContext
from .take import (
    PartTranscriptionRequest,
    PartTranscriptionResult,
    TakeTranscriptionResult,
    transcribe_part as transcribe_part_batch,
    transcribe_take as transcribe_take_batch,
)


@dataclass(frozen=True)
class NotationEngineConfig:
    meter_numerator: int = 4
    meter_denominator: int = 4
    engraving_profile: EngravingProfile = EngravingProfile()

    def validate(self) -> None:
        if self.meter_numerator <= 0 or self.meter_denominator <= 0:
            raise ValueError("meter must be positive")
        self.engraving_profile.validate()


class NotationEngine:
    """Source-neutral API for notation intelligence.

    RealSolo, a standalone desktop app, a web app, or a future audio adapter can
    all call the same engine without the engine knowing which product invoked
    it.
    """

    def __init__(self, config: NotationEngineConfig = NotationEngineConfig()):
        config.validate()
        self.config = config

    def resolve_instrument(self, name: str) -> InstrumentProfile | None:
        return resolve_instrument_profile(name)

    def project_pitched_event(
        self,
        event: CommittedPerformanceEvent,
        *,
        part_id: str,
        staffs: tuple[StaffProfile, ...],
        spelling_context: PitchSpellingContext = PitchSpellingContext(),
        directive: InstrumentNotationDirective | None = None,
    ) -> EventProjectionResult:
        profile = self.resolve_instrument(event.instrument)
        return project_pitched_event(
            event,
            part_id=part_id,
            staffs=staffs,
            spelling_context=spelling_context,
            directive=directive,
            transposition=(
                profile.transposition
                if profile is not None
                else TranspositionSpec()
            ),
            meter_numerator=self.config.meter_numerator,
            meter_denominator=self.config.meter_denominator,
        )

    def chart_position(
        self,
        chart: ChordChart,
        *,
        measure_number: int,
        beat,
    ) -> ChordChartPosition:
        return chart_position(
            chart,
            measure_number=measure_number,
            beat=beat,
        )

    def transpose_chart(
        self,
        chart: ChordChart,
        semitones: int,
        *,
        enharmonic_policy: EnharmonicPolicy | None = None,
    ) -> ChordChart:
        return chart.transpose(
            semitones,
            enharmonic_policy=enharmonic_policy,
        )

    def dynamic_trajectory(
        self,
        events: tuple[CommittedPerformanceEvent, ...],
    ) -> DynamicTrajectoryCandidate:
        return infer_dynamic_trajectory(events)

    def dynamic_spanner(
        self,
        candidate: DynamicTrajectoryCandidate,
        *,
        part_id: str,
        score_events: tuple[ScoreEvent, ...],
        spanner_id: str | None = None,
    ) -> ScoreSpanner | None:
        return score_spanner_from_dynamic_trajectory(
            candidate,
            part_id=part_id,
            score_events=score_events,
            spanner_id=spanner_id,
        )

    def transcribe_part(
        self,
        request: PartTranscriptionRequest,
    ) -> PartTranscriptionResult:
        return transcribe_part_batch(
            request,
            meter_numerator=self.config.meter_numerator,
            meter_denominator=self.config.meter_denominator,
        )

    def transcribe_take(
        self,
        requests: tuple[PartTranscriptionRequest, ...],
        *,
        score_id: str,
        title: str,
        key_signature=None,
    ) -> TakeTranscriptionResult:
        from .score import ScoreKeySignature

        return transcribe_take_batch(
            requests,
            score_id=score_id,
            title=title,
            meter_numerator=self.config.meter_numerator,
            meter_denominator=self.config.meter_denominator,
            key_signature=(
                key_signature
                if key_signature is not None
                else ScoreKeySignature()
            ),
        )

    def transcribe_take_musicxml(
        self,
        requests: tuple[PartTranscriptionRequest, ...],
        *,
        score_id: str,
        title: str,
        key_signature=None,
    ) -> tuple[TakeTranscriptionResult, str]:
        result = self.transcribe_take(
            requests,
            score_id=score_id,
            title=title,
            key_signature=key_signature,
        )
        return result, self.musicxml(result.score)

    def engraving_plan(self, score: ReadableScore) -> EngravingPlan:
        return build_default_engraving_plan(
            score,
            profile=self.config.engraving_profile,
        )

    def audit(self, score: ReadableScore) -> ScoreQualityReport:
        return audit_score_for_performance(score)

    def audit_chart(self, chart: ChordChart) -> ChordChartAudit:
        return audit_chord_chart(chart)

    def render_chart(
        self,
        chart: ChordChart,
        *,
        position: ChordChartPosition | None = None,
        measures_per_row: int = 4,
        transpose_semitones: int = 0,
        enharmonic_policy: EnharmonicPolicy | None = None,
    ) -> ChordChartRenderModel:
        return build_chord_chart_render_model(
            chart,
            position=position,
            measures_per_row=measures_per_row,
            transpose_semitones=transpose_semitones,
            enharmonic_policy=enharmonic_policy,
        )

    def chart_viewport(
        self,
        model: ChordChartRenderModel,
        *,
        config: ChordChartViewportConfig = ChordChartViewportConfig(),
        previous: ChordChartViewport | None = None,
        previous_section: str | None = None,
    ) -> ChordChartViewport:
        return build_chord_chart_viewport(
            model,
            config=config,
            previous=previous,
            previous_section=previous_section,
        )

    def musicxml(
        self,
        score: ReadableScore,
        *,
        engraving_plan: EngravingPlan | None = None,
    ) -> str:
        plan = engraving_plan if engraving_plan is not None else self.engraving_plan(score)
        return score_to_musicxml(score, plan)
