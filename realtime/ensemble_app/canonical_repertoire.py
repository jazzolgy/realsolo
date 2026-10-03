"""Small public-safe chord-form fixtures for canonical runtime tests.

These fixtures contain harmony/form only. They intentionally do not embed
copyrighted melodies or recorded-note transcriptions.
"""
from __future__ import annotations

from .chart import ChartBar, SongChart


AUTUMN_LEAVES_G_MINOR_JAM = SongChart(
    title="Autumn Leaves — G minor jam-session study",
    tempo_bpm=172.0,
    beats_per_bar=4,
    beat_unit=4,
    choruses=1,
    bars=(
        ChartBar(("Cm7",), section="A"),
        ChartBar(("F7",), section="A"),
        ChartBar(("Bbmaj7",), section="A"),
        ChartBar(("Ebmaj7",), section="A"),
        ChartBar(("Am7b5",), section="A"),
        ChartBar(("D7",), section="A"),
        ChartBar(("Gm",), section="A"),
        ChartBar(("Gm",), section="A"),
        ChartBar(("Cm7",), section="A"),
        ChartBar(("F7",), section="A"),
        ChartBar(("Bbmaj7",), section="A"),
        ChartBar(("Ebmaj7",), section="A"),
        ChartBar(("Am7b5",), section="A"),
        ChartBar(("D7",), section="A"),
        ChartBar(("Gm",), section="A"),
        ChartBar(("Gm",), section="A"),
        ChartBar(("Am7b5",), section="B"),
        ChartBar(("D7",), section="B"),
        ChartBar(("Gm",), section="B"),
        ChartBar(("Gm",), section="B"),
        ChartBar(("Cm7",), section="B"),
        ChartBar(("F7",), section="B"),
        ChartBar(("Bbmaj7",), section="B"),
        ChartBar(("Ebmaj7",), section="B"),
        ChartBar(("Am7b5",), section="B"),
        ChartBar(("D7",), section="B"),
        ChartBar(("Gm", "C7"), section="B"),
        ChartBar(("Fm7", "Bb7"), section="B"),
        ChartBar(("Ebmaj7",), section="B"),
        ChartBar(("Am7b5", "D7"), section="B"),
        ChartBar(("Gm",), section="B"),
        ChartBar(("Gm",), section="B"),
    ),
)
