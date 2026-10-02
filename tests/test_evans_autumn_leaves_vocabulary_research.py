import json
from pathlib import Path

ALIGN=Path("research/legends/bill_evans/observations/alignment/AUTUMN_LEAVES_TAKE1_ALIGNMENT_V0_1.json")
VOCAB=Path("research/legends/bill_evans/vocabulary/AUTUMN_LEAVES_ABSTRACT_VOCABULARY_SEED_V0_1.json")


def test_evans_vocab_points_to_take_specific_alignment():
    a=json.loads(ALIGN.read_text(encoding="utf-8"))
    v=json.loads(VOCAB.read_text(encoding="utf-8"))
    assert v["recording_id"]=="bill_evans_portrait_in_jazz_autumn_leaves_take1"
    assert "take1" in a["alignment_id"]
    assert v["alignment_ref"].endswith("AUTUMN_LEAVES_TAKE1_ALIGNMENT_V0_1.json")


def test_evans_vocab_is_abstract_not_literal_solo_storage():
    v=json.loads(VOCAB.read_text(encoding="utf-8"))
    forbidden={"pitches","literal_notes","note_sequence","future_notes","full_transcription"}
    for item in v["items"]:
        assert not forbidden & set(item)
        assert "operation" in item
        assert item["provenance"]


def test_first_evans_seed_covers_motif_and_rhythm_development():
    v=json.loads(VOCAB.read_text(encoding="utf-8"))
    domains={d for item in v["items"] for d in item["domains"]}
    assert "motif_development" in domains
    assert "repetition_variation" in domains
    assert "rhythm_subdivision" in domains
    assert "phrase_entrance" in domains


def test_no_evans_item_freezes_future_phrase():
    v=json.loads(VOCAB.read_text(encoding="utf-8"))
    serialized=json.dumps(v).lower()
    assert '"future_notes"' not in serialized
    assert '"phrase_sequence"' not in serialized
