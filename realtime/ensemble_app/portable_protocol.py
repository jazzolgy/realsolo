from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping

from .player_contract import RenderGesture, RenderVoice

PORTABLE_RUNTIME_PROTOCOL_VERSION = 1
MESSAGE_TYPE_RENDER_GESTURE = "render_gesture"


@dataclass(frozen=True, slots=True)
class PortableRenderPacket:
    """Language-neutral envelope passed from portable musical core to audio runtime.

    The packet contains no sample IDs, file paths, synth programs, or DSP policy.
    Those remain Native Audio Runtime concerns.
    """

    sequence_id: int
    generation: int
    tempo_bpm: float
    anchor_beat: float
    gesture: RenderGesture
    protocol_version: int = PORTABLE_RUNTIME_PROTOCOL_VERSION
    message_type: str = MESSAGE_TYPE_RENDER_GESTURE

    def validate(self) -> None:
        if self.protocol_version != PORTABLE_RUNTIME_PROTOCOL_VERSION:
            raise ValueError("unsupported portable runtime protocol version")
        if self.message_type != MESSAGE_TYPE_RENDER_GESTURE:
            raise ValueError("unsupported portable runtime message type")
        if self.sequence_id < 0:
            raise ValueError("sequence_id cannot be negative")
        if self.generation < 0:
            raise ValueError("generation cannot be negative")
        if not 20.0 <= self.tempo_bpm <= 400.0:
            raise ValueError("tempo_bpm must be within 20..400")
        if self.anchor_beat < 0:
            raise ValueError("anchor_beat cannot be negative")
        self.gesture.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "protocol_version": self.protocol_version,
            "message_type": self.message_type,
            "sequence_id": self.sequence_id,
            "generation": self.generation,
            "transport": {
                "tempo_bpm": self.tempo_bpm,
                "anchor_beat": self.anchor_beat,
            },
            "gesture": self.gesture.to_dict(),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PortableRenderPacket":
        if int(payload.get("protocol_version", -1)) != PORTABLE_RUNTIME_PROTOCOL_VERSION:
            raise ValueError("unsupported portable runtime protocol version")
        if payload.get("message_type") != MESSAGE_TYPE_RENDER_GESTURE:
            raise ValueError("unsupported portable runtime message type")

        transport = payload.get("transport")
        gesture_payload = payload.get("gesture")
        if not isinstance(transport, Mapping) or not isinstance(gesture_payload, Mapping):
            raise ValueError("transport and gesture are required objects")

        def parse_voice(value: Mapping[str, Any]) -> RenderVoice:
            controls = value.get("expression_controls", {})
            if not isinstance(controls, Mapping):
                raise ValueError("expression_controls must be an object")
            return RenderVoice(
                pitch_midi=int(value["pitch_midi"]),
                velocity=int(value.get("velocity", 72)),
                duration_beats=float(value.get("duration_beats", 0.5)),
                onset_offset_beats=float(value.get("onset_offset_beats", 0.0)),
                articulation=tuple(str(x) for x in value.get("articulation", ())),
                instrument_role=str(value.get("instrument_role", "solo")),
                breath_before_beats=float(value.get("breath_before_beats", 0.0)),
                attack_scale=float(value.get("attack_scale", 1.0)),
                release_shape=str(value.get("release_shape", "normal")),
                expression_controls=dict(controls),
            )

        gesture = RenderGesture(
            role=str(gesture_payload["role"]),
            voices=tuple(parse_voice(x) for x in gesture_payload.get("voices", ())),
            drum_hits=tuple(parse_voice(x) for x in gesture_payload.get("drum_hits", ())),
            source=str(gesture_payload.get("source", "player")),
            tags=tuple(str(x) for x in gesture_payload.get("tags", ())),
            annotations={
                str(k): str(v)
                for k, v in dict(gesture_payload.get("annotations", {})).items()
            },
        )
        packet = cls(
            sequence_id=int(payload["sequence_id"]),
            generation=int(payload["generation"]),
            tempo_bpm=float(transport["tempo_bpm"]),
            anchor_beat=float(transport["anchor_beat"]),
            gesture=gesture,
            protocol_version=int(payload["protocol_version"]),
            message_type=str(payload["message_type"]),
        )
        packet.validate()
        return packet

    @classmethod
    def from_json(cls, payload: str) -> "PortableRenderPacket":
        value = json.loads(payload)
        if not isinstance(value, dict):
            raise ValueError("portable runtime packet must be a JSON object")
        return cls.from_dict(value)
