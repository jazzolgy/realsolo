from music_intelligence.corpus import (
    CorpusAccess,
    CorpusItem,
    CorpusKind,
    CorpusRegistry,
    CorpusUse,
    RightsProfile,
)


def parker_audio():
    return CorpusItem(
        item_id="audio.parker.example_take",
        kind=CorpusKind.AUDIO_FOUNDATION,
        media_type="audio",
        title="Parker research take",
        artist_or_source="Charlie Parker",
        local_relpath="audio/parker/example_take.wav",
        access=CorpusAccess.LOCAL_PRIVATE,
        uses=frozenset({CorpusUse.RESEARCH, CorpusUse.REFERENCE}),
        tags=frozenset({"jazz", "bebop", "ensemble"}),
        instruments=frozenset({"alto_sax", "piano", "bass", "drums"}),
        legend_ids=frozenset({"charlie_parker"}),
        rights=RightsProfile(
            source="user research corpus",
            training_permission=None,
            research_permission=True,
            redistribution_permission=False,
        ),
    )


def test_one_shared_item_is_queryable_by_multiple_instruments():
    r = CorpusRegistry((parker_audio(),))
    for instrument in ("alto_sax", "piano", "bass", "drums"):
        items = r.query(
            kind=CorpusKind.AUDIO_FOUNDATION,
            use=CorpusUse.RESEARCH,
            instrument=instrument,
        )
        assert [x.item_id for x in items] == ["audio.parker.example_take"]


def test_registry_does_not_duplicate_same_item_per_player():
    r = CorpusRegistry((parker_audio(),))
    assert len(r.all()) == 1
    assert r.get("audio.parker.example_take").legend_ids == frozenset({"charlie_parker"})


def test_explicit_permission_filter_blocks_unknown_training_rights():
    r = CorpusRegistry((parker_audio(),))
    assert r.query(
        use=CorpusUse.TRAINING,
        require_explicit_permission=True,
    ) == ()


def test_research_permission_can_be_explicitly_filtered():
    r = CorpusRegistry((parker_audio(),))
    items = r.query(
        use=CorpusUse.RESEARCH,
        require_explicit_permission=True,
    )
    assert len(items) == 1


def test_derived_items_keep_lineage():
    audio = parker_audio()
    analysis = CorpusItem(
        item_id="analysis.parker.example_take",
        kind=CorpusKind.MUSICAL_INTELLIGENCE,
        media_type="analysis",
        title="Derived Parker analysis",
        local_relpath="derived/parker/example_take.json",
        access=CorpusAccess.LOCAL_PRIVATE,
        uses=frozenset({CorpusUse.RESEARCH}),
        derived_from=(audio.item_id,),
        rights=RightsProfile(research_permission=True),
    )
    r = CorpusRegistry((audio, analysis))
    closure = r.dependency_closure(analysis.item_id)
    assert [x.item_id for x in closure] == [
        "audio.parker.example_take",
        "analysis.parker.example_take",
    ]


def test_local_path_uses_one_shared_root(tmp_path):
    r = CorpusRegistry((parker_audio(),))
    path = r.resolve_path("audio.parker.example_take", root=tmp_path)
    assert str(path).endswith("audio/parker/example_take.wav")
