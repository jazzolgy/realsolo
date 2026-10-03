from __future__ import annotations

import time
from dataclasses import dataclass

from .models import MidiObservation, ObservationKind, TransportEvent


class MidiBackendUnavailable(RuntimeError):
    pass


def _mido():
    try:
        import mido
    except ImportError as exc:
        raise MidiBackendUnavailable('Install MIDI support with: pip install -e ".[midi]"') from exc
    return mido


def list_ports() -> tuple[list[str], list[str]]:
    mido = _mido()
    return list(mido.get_input_names()), list(mido.get_output_names())


@dataclass
class MidoSink:
    output_name: str

    def __post_init__(self) -> None:
        self.port = None

    def open(self) -> "MidoSink":
        self.port = _mido().open_output(self.output_name)
        return self

    def close(self) -> None:
        if self.port is not None:
            self.port.close()
            self.port = None

    def __call__(self, event: TransportEvent) -> None:
        if self.port is None:
            raise RuntimeError("MIDI output is not open")
        msg = _mido().Message(
            event.kind,
            note=event.pitch_midi,
            velocity=event.velocity,
            channel=event.channel,
        )
        self.port.send(msg)


def convert_message(msg, timestamp: float) -> MidiObservation | None:
    if msg.type == "note_on":
        velocity = int(getattr(msg, "velocity", 0))
        kind = ObservationKind.NOTE_ON if velocity > 0 else ObservationKind.NOTE_OFF
        return MidiObservation(timestamp, kind, note=msg.note, velocity=velocity, channel=msg.channel)
    if msg.type == "note_off":
        return MidiObservation(timestamp, ObservationKind.NOTE_OFF, note=msg.note, velocity=0, channel=msg.channel)
    if msg.type == "control_change":
        return MidiObservation(
            timestamp,
            ObservationKind.CONTROL_CHANGE,
            channel=msg.channel,
            control=msg.control,
            value=msg.value,
        )
    return None


def live_poll(input_name: str, on_observation, on_tick, *, tick_s: float = 0.010) -> None:
    mido = _mido()
    with mido.open_input(input_name) as port:
        while True:
            now = time.monotonic()
            for msg in port.iter_pending():
                obs = convert_message(msg, time.monotonic())
                if obs is not None:
                    on_observation(obs)
            on_tick(now)
            time.sleep(tick_s)
