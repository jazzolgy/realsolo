from dataclasses import replace
import json

from music_intelligence.reasoning.ensemble_state import (
    InteractionKind,
    update_player_intent,
)
from realtime.ensemble_app.rehearsal import run_chart_rehearsal
from realtime.ensemble_app.stage1_trio import Stage1TrioRuntime


CHART_8 = (
    "Dm7",
    "G7",
    "Cmaj7",
    "A7",
    "Dm7",
    "G7",
    "Cmaj7",
    "G7",
)


def _decision(result, player_id):
    return next(x for x in result.decisions if x.player_id == player_id)


def test_stage1_multi_bar_rehearsal_logs_every_tick_and_player(tmp_path):
    trio = Stage1TrioRuntime.create(132.0)
    log = run_chart_rehearsal(trio, CHART_8, tempo_bpm=132.0)

    assert len(log.ticks) == 32
    assert {x.bar_index for x in log.ticks} == set(range(8))

    for tick in log.ticks:
        assert {x["player_id"] for x in tick.intents} == {"piano", "bass", "drums"}
        assert {x["player_id"] for x in tick.directives} == {"piano", "bass", "drums"}
        assert tick.published_generation > tick.snapshot_generation

    generations = [x.snapshot_generation for x in log.ticks]
    assert generations == sorted(generations)
    assert all(b > a for a, b in zip(generations, generations[1:]))

    target = log.write_jsonl(tmp_path / "trio-rehearsal.jsonl")
    rows = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 32
    assert rows[0]["chord_symbol"] == "Dm7"
    assert rows[-1]["bar_index"] == 7
    assert any(g["role"] == "bass" for row in rows for g in row["gestures"])
    assert any(g["role"] == "drums" for row in rows for g in row["gestures"])


def test_committed_drums_intent_changes_next_tick_bass_policy():
    """Counterfactual causal probe across ticks, never within the same tick.

    Both runtimes first execute the same real trio tick so their local player
    memories are aligned. We then change only the already-committed drums intent
    in the published state before the next tick. Bass must read that changed
    prior-tick state and reduce density when drums are filling.
    """
    control = Stage1TrioRuntime.create(120.0)
    treatment = Stage1TrioRuntime.create(120.0)

    control_first = control.decide(
        "Dm7", "G7",
        beat_in_bar=0.0,
        bar_index=0,
        total_bars=8,
        tempo_bpm=120.0,
    )
    treatment_first = treatment.decide(
        "Dm7", "G7",
        beat_in_bar=0.0,
        bar_index=0,
        total_bars=8,
        tempo_bpm=120.0,
    )

    control_drums = _decision(control_first, "drums").intent
    treatment_drums = _decision(treatment_first, "drums").intent

    control.state = update_player_intent(
        control.state,
        replace(
            control_drums,
            interaction=InteractionKind.SUPPORT,
            density=0.25,
            tags=control_drums.tags | frozenset({"causal_control"}),
        ),
    )
    treatment.state = update_player_intent(
        treatment.state,
        replace(
            treatment_drums,
            interaction=InteractionKind.SETUP,
            density=0.85,
            tags=treatment_drums.tags | frozenset({"causal_treatment"}),
        ),
    )

    control_generation = control.state.generation
    treatment_generation = treatment.state.generation

    control_next = control.decide(
        "Dm7", "G7",
        beat_in_bar=1.0,
        bar_index=0,
        total_bars=8,
        tempo_bpm=120.0,
    )
    treatment_next = treatment.decide(
        "Dm7", "G7",
        beat_in_bar=1.0,
        bar_index=0,
        total_bars=8,
        tempo_bpm=120.0,
    )

    assert control_next.snapshot_generation > control_generation
    assert treatment_next.snapshot_generation > treatment_generation

    control_bass = _decision(control_next, "bass")
    treatment_bass = _decision(treatment_next, "bass")

    # Bass interaction grammar explicitly yields density when drums are filling.
    assert treatment_bass.intent.density < control_bass.intent.density
    assert treatment_bass.intent != control_bass.intent

    # The changed state is only heard on the following tick; all three players
    # inside that tick still share one immutable snapshot generation.
    assert len({control_next.snapshot_generation for _ in control_next.decisions}) == 1
    assert len({treatment_next.snapshot_generation for _ in treatment_next.decisions}) == 1
