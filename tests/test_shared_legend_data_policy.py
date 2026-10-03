from music_intelligence.legends import (
    LegendDataLayer,
    LegendMaterialKind,
    PrivateLegendStoreDescriptor,
    default_legend_data_layer,
    may_publish_material,
)


def test_exact_legend_material_defaults_private():
    assert default_legend_data_layer(
        LegendMaterialKind.SOURCE_AUDIO
    ) is LegendDataLayer.PRIVATE_RAW
    assert default_legend_data_layer(
        LegendMaterialKind.EXACT_TRANSCRIPTION
    ) is LegendDataLayer.PRIVATE_RAW
    assert default_legend_data_layer(
        LegendMaterialKind.EXACT_SCORE_PHRASE
    ) is LegendDataLayer.PRIVATE_RAW
    assert default_legend_data_layer(
        LegendMaterialKind.NORMALIZED_PHRASE
    ) is LegendDataLayer.PRIVATE_DERIVED
    assert default_legend_data_layer(
        LegendMaterialKind.LITERAL_VOCABULARY
    ) is LegendDataLayer.PRIVATE_DERIVED


def test_public_runtime_safe_material_is_publishable():
    for kind in (
        LegendMaterialKind.ABSTRACT_VOCABULARY,
        LegendMaterialKind.MOTIF_IDENTITY,
        LegendMaterialKind.STYLE_TENDENCY,
        LegendMaterialKind.POLICY_PRIOR,
        LegendMaterialKind.NON_RECONSTRUCTIVE_STATISTICS,
        LegendMaterialKind.PROVENANCE_MANIFEST,
    ):
        assert may_publish_material(kind) is True


def test_private_exact_material_is_not_public_by_default():
    for kind in (
        LegendMaterialKind.SOURCE_AUDIO,
        LegendMaterialKind.EXACT_TRANSCRIPTION,
        LegendMaterialKind.EXACT_SCORE_PHRASE,
        LegendMaterialKind.NORMALIZED_PHRASE,
        LegendMaterialKind.LITERAL_VOCABULARY,
        LegendMaterialKind.SIMILARITY_FINGERPRINT,
    ):
        assert may_publish_material(kind) is False


def test_private_store_descriptor_exposes_capability_not_exact_payload():
    descriptor = PrivateLegendStoreDescriptor(
        store_id="private.legend.lafaro.v1",
        legend_id="scott_lafaro",
        supports_literal_vocabulary=True,
        supports_exact_transcription=True,
        supports_similarity_fingerprints=True,
        provenance=("private_store_manifest",),
    )
    descriptor.validate()
    assert descriptor.legend_id == "scott_lafaro"
    assert not hasattr(descriptor, "literal_representation")
    assert not hasattr(descriptor, "pitch_midi")
