from dataclasses import dataclass

from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    InteractionEvent,
    InteractionKind,
    PlayerPresence,
    PlayerRole,
    TransportState,
)

from realtime.ensemble_app.player_contract import RenderGesture, RenderVoice
from realtime.ensemble_app.runtime_loop import (
    EnsembleRuntimeLoop,
    PlayerRuntimeDecision,
    committed_intent,
)


def base_state():
    return EnsembleState(
        transport=TransportState(beat=1.0, bar=0, section="A"),
        players=(
            PlayerPresence("piano", "piano", PlayerRole.COMPER),
            PlayerPresence("bass", "bass", PlayerRole.BASS),
            PlayerPresence("drums", "drums", PlayerRole.DRUMS),
        ),
    )


@dataclass
class FakeProvider:
    player_id: str
    pitch: int
    seen_generations: list[int]

    def decide_immediate(self, *, snapshot, directive, context):
        self.seen_generations.append(snapshot.generation)
        gesture = RenderGesture(
            role=self.player_id,
            voices=(
                RenderVoice(
                    self.pitch,
                    duration_beats=.5,
                    instrument_role=self.player_id,
                ),
            ) if self.player_id != "drums" else (),
            drum_hits=(
                RenderVoice(
                    51,
                    duration_beats=.1,
                    instrument_role="drums",
                ),
            ) if self.player_id == "drums" else (),
            source=f"player/{self.player_id}",
            tags=(directive.interaction.value,),
        )
        intent = committed_intent(
            player_id=self.player_id,
            directive=directive,
            density=.4,
            energy=.5,
            tension=.4,
            leadership=.0,
        )
        return PlayerRuntimeDecision(
            player_id=self.player_id,
            intent=intent,
            gestures=(gesture,),
            interaction_events=(
                InteractionEvent(
                    self.player_id,
                    directive.interaction,
                    target_player_ids=directive.target_player_ids,
                ),
            ),
        )


def test_all_players_decide_from_same_snapshot_generation():
    seen_piano, seen_bass, seen_drums = [], [], []
    loop = EnsembleRuntimeLoop((
        FakeProvider("piano", 60, seen_piano),
        FakeProvider("bass", 36, seen_bass),
        FakeProvider("drums", 0, seen_drums),
    ))
    result = loop.step(base_state())
    assert seen_piano == [0]
    assert seen_bass == [0]
    assert seen_drums == [0]
    assert result.snapshot_generation == 0


def test_publication_happens_after_provider_decisions():
    loop = EnsembleRuntimeLoop((
        FakeProvider("piano", 60, []),
        FakeProvider("bass", 36, []),
        FakeProvider("drums", 0, []),
    ))
    result = loop.step(base_state())
    assert len(result.decisions) == 3
    assert len(result.gestures) == 3
    assert result.state.generation > result.snapshot_generation
    assert result.state.intent_for("piano") is not None
    assert result.state.intent_for("bass") is not None
    assert result.state.intent_for("drums") is not None


def test_missing_provider_does_not_block_other_players():
    loop = EnsembleRuntimeLoop((FakeProvider("bass", 36, []),))
    result = loop.step(base_state())
    assert result.skipped_player_ids == ("piano", "drums")
    assert [x.player_id for x in result.decisions] == ["bass"]


def test_player_cannot_commit_for_another_player():
    class BadProvider:
        player_id = "piano"

        def decide_immediate(self, *, snapshot, directive, context):
            intent = committed_intent(
                player_id="bass",
                directive=directive,
                density=.3,
                energy=.3,
                tension=.3,
                leadership=.0,
            )
            return PlayerRuntimeDecision("piano", intent)

    loop = EnsembleRuntimeLoop((BadProvider(),))
    try:
        loop.step(base_state())
    except ValueError as e:
        assert "intent must belong" in str(e)
    else:
        raise AssertionError("expected validation error")


def test_runtime_loop_commits_only_immediate_renderer_gestures():
    loop = EnsembleRuntimeLoop((
        FakeProvider("piano", 60, []),
        FakeProvider("bass", 36, []),
        FakeProvider("drums", 0, []),
    ))
    result = loop.step(base_state())
    assert not hasattr(result, "future_score")
    assert not hasattr(result, "future_notes")
    for gesture in result.gestures:
        assert isinstance(gesture, RenderGesture)


def test_runtime_tick_projects_committed_gestures_to_portable_packets():
    loop = EnsembleRuntimeLoop((
        FakeProvider("piano", 60, []),
        FakeProvider("bass", 36, []),
        FakeProvider("drums", 0, []),
    ))
    result = loop.step(base_state())
    packets = result.to_portable_packets(sequence_start=100)

    assert [p.sequence_id for p in packets] == [100, 101, 102]
    assert all(p.protocol_version == 1 for p in packets)
    assert all(p.generation == result.snapshot_generation for p in packets)
    assert all(p.anchor_beat == result.state.transport.beat for p in packets)
    assert [p.gesture.role for p in packets] == ["piano", "bass", "drums"]



def test_quartet_players_all_read_same_immutable_snapshot():
    state=EnsembleState(
        transport=TransportState(beat=1.0,bar=0,section="A"),
        players=(
            PlayerPresence("piano","piano",PlayerRole.COMPER),
            PlayerPresence("bass","bass",PlayerRole.BASS),
            PlayerPresence("drums","drums",PlayerRole.DRUMS),
            PlayerPresence("sax","tenor_sax",PlayerRole.SOLOIST),
        ),
    )
    seen={name:[] for name in ("piano","bass","drums","sax")}
    loop=EnsembleRuntimeLoop(tuple(
        FakeProvider(
            name,
            {"piano":60,"bass":36,"drums":0,"sax":67}[name],
            seen[name],
        )
        for name in ("piano","bass","drums","sax")
    ))
    result=loop.step(state)
    assert seen == {
        "piano":[0],
        "bass":[0],
        "drums":[0],
        "sax":[0],
    }
    assert {d.player_id for d in result.decisions} == {"piano","bass","drums","sax"}
