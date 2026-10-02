from __future__ import annotations

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .chart import ChartBar, SongChart
from .harmony_display import transpose_chord
from .stage1_music import Stage1Soloist, accompaniment_frame
from .player_contract import fallback_accompaniment_gesture, monophonic_solo_gesture
from .player_provider import current_stage1_provider_status

WEB_ROOT = Path(__file__).with_name("web")


def demo_chart() -> SongChart:
    return SongChart(
        title="RealSolo ii–V–I Lab",
        tempo_bpm=120.0,
        beats_per_bar=4,
        choruses=3,
        bars=(
            ChartBar(("Dm7",), section="A", rehearsal_mark="A"),
            ChartBar(("G7",), section="A"),
            ChartBar(("Cmaj7",), section="A"),
            ChartBar(("Cmaj7",), section="A"),
            ChartBar(("Em7",), section="B", rehearsal_mark="B"),
            ChartBar(("A7",), section="B"),
            ChartBar(("Dm7", "G7"), section="B"),
            ChartBar(("Cmaj7",), section="B"),
        ),
    )


def chart_payload(chart: SongChart, *, transpose: int = 0) -> dict:
    return {
        "title": chart.title,
        "tempo_bpm": chart.tempo_bpm,
        "beats_per_bar": chart.beats_per_bar,
        "beat_unit": chart.beat_unit,
        "choruses": chart.choruses,
        "transpose": transpose,
        "bars": [
            {
                "chords": [transpose_chord(chord, transpose) for chord in bar.chords],
                "section": bar.section,
                "rehearsal_mark": bar.rehearsal_mark,
            }
            for bar in chart.bars
        ],
    }


class Stage1Handler(SimpleHTTPRequestHandler):
    chart = demo_chart()
    soloist = Stage1Soloist()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/player-status":
            body = json.dumps(
                [status.to_dict() for status in current_stage1_provider_status()]
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/api/reset-solo":
            self.soloist.reset()
            body = b'{"ok": true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/api/accompaniment":
            query = parse_qs(parsed.query)
            chord = query.get("chord", ["Cmaj7"])[0]
            try:
                beat = int(query.get("beat", ["0"])[0]) % 4
            except ValueError:
                beat = 0
            frame = accompaniment_frame(chord, beat)
            body = json.dumps(
                {
                    "legacy": frame,
                    "gesture": fallback_accompaniment_gesture(frame).to_dict(),
                }
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/api/solo-event":
            query = parse_qs(parsed.query)
            chord = query.get("chord", ["Cmaj7"])[0]
            next_chord = query.get("next_chord", [""])[0]
            try:
                beat_in_bar = float(query.get("beat_in_bar", ["0"])[0])
                phrase_step = int(query.get("phrase_step", ["0"])[0])
            except ValueError:
                beat_in_bar, phrase_step = 0.0, 0
            decision = self.soloist.choose(
                chord,
                next_chord,
                beat_in_bar=beat_in_bar,
                phrase_step=phrase_step,
            )
            gesture = (
                monophonic_solo_gesture(
                    decision["pitch"],
                    decision["duration_beats"],
                    source=decision["source_family"] or "core_immediate",
                ).to_dict()
                if decision["pitch"] is not None
                else None
            )
            body = json.dumps(
                {
                    **decision,
                    "gesture": gesture,
                }
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/api/chart":
            query = parse_qs(parsed.query)
            try:
                transpose = max(-12, min(12, int(query.get("transpose", ["0"])[0])))
            except ValueError:
                transpose = 0
            body = json.dumps(chart_payload(self.chart, transpose=transpose)).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def log_message(self, format, *args):
        return


def run_stage1_web(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), Stage1Handler)
    print(f"RealSolo Stage 1: http://{host}:{port}")
    print("Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
