"""Viewport planning for live chord-chart auto-follow.

This layer decides which render rows should be visible/prefetched and which row
is the current follow target.  It does not perform scrolling or animation.
"""
from __future__ import annotations

from dataclasses import dataclass

from .chord_chart_render import ChordChartRenderModel, ChordChartRenderRow


@dataclass(frozen=True)
class ChordChartViewportConfig:
    visible_row_count: int = 2
    prefetch_before: int = 1
    prefetch_after: int = 2
    keep_current_row_slot: int = 0

    def validate(self) -> None:
        if self.visible_row_count <= 0:
            raise ValueError("visible_row_count must be positive")
        if self.prefetch_before < 0 or self.prefetch_after < 0:
            raise ValueError("prefetch counts may not be negative")
        if not 0 <= self.keep_current_row_slot < self.visible_row_count:
            raise ValueError("keep_current_row_slot must fit visible_row_count")


@dataclass(frozen=True)
class ChordChartViewport:
    active_row_index: int | None
    visible_rows: tuple[ChordChartRenderRow, ...]
    prefetched_rows: tuple[ChordChartRenderRow, ...]
    follow_target_row_index: int | None
    section_changed: bool = False
    should_advance: bool = False


def active_row_index(model: ChordChartRenderModel) -> int | None:
    if model.current_measure_number is None:
        return None
    for row in model.rows:
        if any(
            measure.measure_number == model.current_measure_number
            for measure in row.measures
        ):
            return row.row_index
    raise ValueError("current measure not present in render rows")


def build_chord_chart_viewport(
    model: ChordChartRenderModel,
    *,
    config: ChordChartViewportConfig = ChordChartViewportConfig(),
    previous: "ChordChartViewport | None" = None,
    previous_section: str | None = None,
) -> ChordChartViewport:
    """Build a stable auto-follow viewport from a chart render model."""

    config.validate()
    if not model.rows:
        return ChordChartViewport(None, (), (), None)

    active = active_row_index(model)
    if active is None:
        start = 0
    else:
        start = max(0, active - config.keep_current_row_slot)
        max_start = max(0, len(model.rows) - config.visible_row_count)
        start = min(start, max_start)

    end = min(len(model.rows), start + config.visible_row_count)
    visible = model.rows[start:end]

    prefetch_start = max(0, start - config.prefetch_before)
    prefetch_end = min(len(model.rows), end + config.prefetch_after)
    prefetched = model.rows[prefetch_start:prefetch_end]

    section_changed = (
        previous_section is not None
        and model.current_section is not None
        and previous_section != model.current_section
    )

    prior_active = previous.active_row_index if previous is not None else None
    should_advance = (
        active is not None
        and prior_active is not None
        and active > prior_active
    )

    return ChordChartViewport(
        active_row_index=active,
        visible_rows=tuple(visible),
        prefetched_rows=tuple(prefetched),
        follow_target_row_index=active,
        section_changed=section_changed,
        should_advance=should_advance,
    )
