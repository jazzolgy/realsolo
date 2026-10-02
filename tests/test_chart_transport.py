from realtime.ensemble_app.chart import ChartBar, SongChart
from realtime.ensemble_app.chart_transport import ChartTransport
from realtime.ensemble_app.session import AIRole, SessionConfig, UserRole


def test_chart_transport_advances_harmony_by_bar():
    chart = SongChart(
        "Test",
        (
            ChartBar(("Cmaj7",)),
            ChartBar(("Dm7", "G7")),
        ),
        tempo_bpm=120,
        beats_per_bar=4,
    )
    transport = ChartTransport(chart)
    transport.start(0.0)

    assert transport.position(0.0).chord_symbol == "Cmaj7"
    assert transport.position(2.1).bar_in_form == 1
    assert transport.position(2.1).chord_symbol == "Dm7"
    assert transport.position(3.1).chord_symbol == "G7"


def test_pianist_comping_role_maps_ai_to_soloist():
    chart = SongChart("Test", (ChartBar(("Cmaj7",)),))
    config = SessionConfig.for_user_role(chart, UserRole.COMPER)
    assert config.ai_role == AIRole.SOLOIST


def test_soloist_role_maps_ai_to_accompaniment():
    chart = SongChart("Test", (ChartBar(("Cmaj7",)),))
    config = SessionConfig.for_user_role(chart, UserRole.SOLOIST)
    assert config.ai_role == AIRole.ACCOMPANIMENT
