from music_intelligence.corpus import ScoreEvidence, ScoreEvidenceKind


def test_scorebook_schema_freezes_cross_player_evidence_kinds():
    required = {
        "feel_change",
        "written_part",
        "navigation",
        "section_role",
        "bass_instruction",
    }
    assert required <= {x.value for x in ScoreEvidenceKind}


def test_evidence_carries_confidence_and_provenance():
    item = ScoreEvidence(
        ScoreEvidenceKind.SECTION_ROLE,
        "solo section",
        confidence=.87,
        source_page=12,
        provenance=("vision:page12", "manual-verified"),
    )
    item.validate()
    assert item.confidence == .87
    assert item.provenance == ("vision:page12", "manual-verified")
