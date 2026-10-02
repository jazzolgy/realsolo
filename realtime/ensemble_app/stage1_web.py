from __future__ import annotations

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .chart import ChartBar, SongChart
from .asset_installer import ASSET_ROOT
from .harmony_display import transpose_chord
from .stage1_music import Stage1Soloist
from .player_contract import monophonic_solo_gesture, apply_shared_groove_to_render_gesture
from music_intelligence.reasoning.groove_context import GrooveFeel, build_groove_context
from .player_provider import current_stage1_provider_status
from .stage1_trio import Stage1TrioRuntime

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


def groove_payload(tempo_bpm: float) -> dict:
    groove=build_groove_context(
        GrooveFeel.SWING,
        tempo_bpm=tempo_bpm,
        grammar_id="swing.eighth_triplet_feel",
        subdivision_hint="swing_eighth",
        provenance=("stage1_web_groove_query",),
    )
    return {
        "feel": groove.feel.value,
        "swing_ratio": groove.effective_swing_ratio,
        "offbeat_fraction": groove.swing_offbeat_fraction,
        "grammar_id": groove.grammar_id,
    }


class Stage1Handler(SimpleHTTPRequestHandler):
    chart = demo_chart()
    soloist = Stage1Soloist()
    trio = Stage1TrioRuntime.create()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/assets/"):
            rel = parsed.path[len("/assets/"):].lstrip("/")
            target = (ASSET_ROOT / rel).resolve()
            root = ASSET_ROOT.resolve()
            if root not in target.parents and target != root:
                self.send_error(403)
                return
            if not target.is_file():
                self.send_error(404)
                return
            ctype = self.guess_type(str(target))
            data = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "public, max-age=31536000")
            self.end_headers()
            self.wfile.write(data)
            return
        if parsed.path == "/api/groove":
            query=parse_qs(parsed.query)
            try:
                tempo=max(40.0,min(360.0,float(query.get("tempo",[str(self.chart.tempo_bpm)])[0])))
            except ValueError:
                tempo=self.chart.tempo_bpm
            body=json.dumps(groove_payload(tempo)).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Content-Length",str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

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
            self.trio.reset(self.chart.tempo_bpm)
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
            next_chord = query.get("next_chord", [""])[0]
            try:
                beat = float(query.get("beat", ["0"])[0]) % self.chart.beats_per_bar
                bar_index = int(query.get("bar_index", ["0"])[0]) % len(self.chart.bars)
                tempo_bpm = float(query.get("tempo", [str(self.chart.tempo_bpm)])[0])
                chorus = max(0, int(query.get("chorus", ["0"])[0]))
            except ValueError:
                beat, bar_index, tempo_bpm, chorus = 0.0, 0, self.chart.tempo_bpm, 0

            players_raw=query.get("players",[""])[0].strip()
            active_player_ids=(
                frozenset(x.strip() for x in players_raw.split(",") if x.strip())
                if players_raw else None
            )

            bar = self.chart.bars[bar_index]
            result = self.trio.decide(
                chord,
                next_chord,
                beat_in_bar=beat,
                bar_index=bar_index,
                total_bars=len(self.chart.bars),
                tempo_bpm=tempo_bpm,
                section=bar.section or "",
                chorus=chorus,
                active_player_ids=active_player_ids,
            )

            combined = {
                "role": "accompaniment",
                "voices": [],
                "drum_hits": [],
                "source": "native_trio_runtime",
                "tags": [],
                "annotations": {
                    "snapshot_generation": str(result.snapshot_generation),
                },
            }
            for gesture in result.gestures:
                payload = gesture.to_dict()
                combined["voices"].extend(payload["voices"])
                combined["drum_hits"].extend(payload["drum_hits"])
                combined["tags"].extend(payload["tags"])
                combined["annotations"].update(payload["annotations"])

            swing_subbeat = None
            groove=self.trio.state.groove
            if (
                active_player_ids is None
                and groove is not None
                and groove.feel.value in {"swing","shuffle"}
                and abs(beat-round(beat)) < 1e-6
                and int(round(beat)) % 2 == 1
            ):
                offbeat=groove.swing_offbeat_fraction
                sub=self.trio.decide(
                    chord,
                    next_chord,
                    beat_in_bar=(beat+offbeat) % self.chart.beats_per_bar,
                    bar_index=bar_index,
                    total_bars=len(self.chart.bars),
                    tempo_bpm=tempo_bpm,
                    section=bar.section or "",
                    chorus=chorus,
                    active_player_ids=frozenset({"drums"}),
                )
                sub_combined={
                    "role":"drums",
                    "voices":[],
                    "drum_hits":[],
                    "source":"native_trio_runtime:shared_swing_subbeat",
                    "tags":[],
                    "annotations":{
                        "snapshot_generation":str(sub.snapshot_generation),
                        "shared_subbeat":"true",
                    },
                }
                for gesture in sub.gestures:
                    payload=gesture.to_dict()
                    sub_combined["voices"].extend(payload["voices"])
                    sub_combined["drum_hits"].extend(payload["drum_hits"])
                    sub_combined["tags"].extend(payload["tags"])
                    sub_combined["annotations"].update(payload["annotations"])
                swing_subbeat={
                    "offset_beats":offbeat,
                    "gesture":sub_combined,
                }

            body = json.dumps(
                {
                    "gesture": combined,
                    "swing_subbeat": swing_subbeat,
                    "players": [d.player_id for d in result.decisions],
                    "skipped": list(result.skipped_player_ids),
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
            gesture = None
            if decision["pitch"] is not None:
                raw_gesture=monophonic_solo_gesture(
                    decision["pitch"],
                    decision["duration_beats"],
                    velocity=decision.get("velocity", 82),
                    articulation=tuple(decision.get("articulation", ())),
                    instrument_role="tenor_sax",
                    breath_before_beats=0.18 if decision.get("breath_before") else 0.0,
                    attack_scale=float(decision.get("attack_scale", 1.0)),
                    release_shape=decision.get("release_shape", "normal"),
                    source=decision["source_family"] or "core_immediate",
                )
                gesture=apply_shared_groove_to_render_gesture(
                    raw_gesture,
                    anchor_beat=beat_in_bar,
                    groove=self.trio.state.groove,
                ).to_dict()
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
