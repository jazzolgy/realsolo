import json
from dataclasses import fields
from pathlib import Path

import music_intelligence.transcribe.events as events

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/contracts/performance_evidence_v1_expected.json"


def _snapshot():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_performance_evidence_version_matches_snapshot():
    snapshot = _snapshot()
    assert events.CONTRACT_VERSION == snapshot["version"]


def test_required_public_types_still_exist():
    snapshot = _snapshot()
    missing = [name for name in snapshot["required_public_types"] if not hasattr(events, name)]
    assert missing == [], f"contract types missing: {missing}"


def test_required_event_fields_still_exist():
    snapshot = _snapshot()
    actual = {item.name for item in fields(events.CommittedPerformanceEvent)}
    missing = [name for name in snapshot["required_event_fields"] if name not in actual]
    assert missing == [], f"contract fields missing: {missing}"
