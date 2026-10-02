import json
from pathlib import Path

import pytest

from realtime.ensemble_app.portable_protocol import (
    PORTABLE_RUNTIME_PROTOCOL_VERSION,
    PortableRenderPacket,
)


FIXTURE = Path("tests/fixtures/portable_runtime/render_packet_v1.json")
SCHEMA = Path("protocol/portable_render_packet_v1.schema.json")


def test_golden_portable_packet_round_trips_semantically():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    packet = PortableRenderPacket.from_dict(payload)
    emitted = packet.to_dict()

    assert emitted == payload
    assert packet.protocol_version == PORTABLE_RUNTIME_PROTOCOL_VERSION
    assert packet.gesture.voices[0].instrument_role == "tenor_sax"
    assert packet.gesture.voices[0].expression_controls["vibrato_depth"] == .65


def test_portable_json_is_deterministic():
    payload = FIXTURE.read_text(encoding="utf-8")
    packet = PortableRenderPacket.from_json(payload)
    assert PortableRenderPacket.from_json(packet.to_json()).to_dict() == packet.to_dict()


def test_rejects_unknown_protocol_version():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["protocol_version"] = 99
    with pytest.raises(ValueError, match="protocol version"):
        PortableRenderPacket.from_dict(payload)


def test_schema_is_versioned_and_language_neutral():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["properties"]["protocol_version"]["const"] == 1
    voice = schema["$defs"]["renderVoice"]
    assert "expression_controls" in voice["properties"]
    text = SCHEMA.read_text(encoding="utf-8").lower()
    for forbidden in ("python", "soundfont", "coreaudio", "oboe", "aaudio"):
        assert forbidden not in text
