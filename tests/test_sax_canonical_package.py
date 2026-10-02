from players.sax import SoloArticulation, SaxExpressionContext
from players.sax.articulation import SoloArticulation as CanonicalSoloArticulation
from players.sax.expression import SaxExpressionContext as CanonicalExpressionContext


def test_sax_player_package_is_canonical_and_importable():
    assert SoloArticulation is CanonicalSoloArticulation
    assert SaxExpressionContext is CanonicalExpressionContext
