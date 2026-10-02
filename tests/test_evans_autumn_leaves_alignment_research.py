import json
from pathlib import Path


PATH=Path("research/legends/bill_evans/observations/alignment/AUTUMN_LEAVES_TAKE1_ALIGNMENT_V0_1.json")


def load():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_evans_autumn_leaves_alignment_has_32_bar_form():
    data=load()
    assert data["form"]["bars"]==32
    assert data["audio_alignment"]["estimated_chorus_duration_seconds"]>30
    assert data["audio_alignment"]["estimated_chorus_duration_seconds"]<45


def test_alignment_keeps_take_and_provenance_specific():
    data=load()
    assert "take1" in data["alignment_id"]
    assert data["provenance"]
    assert any("master_index" in item for item in data["provenance"])


def test_alignment_does_not_store_literal_melody_or_solo_sequence():
    data=load()
    forbidden={"melody_notes","solo_notes","literal_phrase","note_sequence","future_notes"}
    assert not forbidden & set(data)
    assert "No melody transcription" in data["copyright_boundary"]


def test_piano_solo_entry_is_late_in_third_grid_chorus():
    data=load()
    anchor=next(x for x in data["structural_anchors"] if x["label"]=="piano_solo_entry_hint")
    assert anchor["track_seconds"][0]==120.0
    assert "chorus 3 bars 29-32" in anchor["chorus_grid"]
