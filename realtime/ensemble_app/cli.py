from __future__ import annotations

import argparse
import time

from music_intelligence.reasoning.online_improviser import OnlineMusicalEvaluator, PerformanceMemory

from .audio_io import list_audio_inputs, live_audio_poll
from .core_bridge import CoreImmediateBridge, DiagnosticResponseFactory
from .engine import EnsembleEngine
from .midi_io import MidoSink, list_ports, live_poll
from .models import TransportEvent
from .stage1_web import run_stage1_web
from .research_web import run_research_web
from .asset_installer import PROFILES, activate_profile, install_assets


def _core() -> CoreImmediateBridge:
    return CoreImmediateBridge(
        factory=DiagnosticResponseFactory(),
        evaluator=OnlineMusicalEvaluator(),
        memory=PerformanceMemory(),
    )


def _print_state(state) -> None:
    bpm = f"{state.beat.tempo_bpm:6.1f}" if state.beat.tempo_bpm else "   ?  "
    phase = f"{state.beat.phase:.2f}" if state.beat.phase is not None else "?"
    pitch = f"{state.audio_pitch_hz:.1f}Hz" if state.audio_pitch_hz else "-"
    print(
        f"rev={state.revision:06d} in={state.input_mode:6s} bpm={bpm} phase={phase} "
        f"activity={state.human_activity:.2f} rms={state.audio_rms:.4f} "
        f"pitch={pitch} phrase_end={state.phrase.phrase_end}",
        end="\r",
        flush=True,
    )


def command_ports() -> None:
    try:
        ins, outs = list_ports()
        print("MIDI inputs:")
        print("\n".join(f"  {x}" for x in ins) or "  (none)")
        print("MIDI outputs:")
        print("\n".join(f"  {x}" for x in outs) or "  (none)")
    except Exception as exc:
        print(f"MIDI unavailable: {exc}")

    try:
        print("Audio inputs:")
        for index, name, rate in list_audio_inputs():
            print(f"  [{index}] {name} ({rate:.0f} Hz)")
    except Exception as exc:
        print(f"Audio unavailable: {exc}")


def command_monitor_midi(input_name: str) -> None:
    engine = EnsembleEngine(_core(), lambda _: None)
    try:
        live_poll(input_name, lambda obs: _print_state(engine.ingest(obs)), lambda now: engine.tick(now))
    except KeyboardInterrupt:
        print("\nStopped.")


def command_monitor_audio(device) -> None:
    engine = EnsembleEngine(_core(), lambda _: None)
    last_print = 0.0

    def observe(obs):
        nonlocal last_print
        state = engine.ingest(obs)
        now = time.monotonic()
        if obs.onset or state.phrase.phrase_end or now - last_print > 0.08:
            _print_state(state)
            last_print = now

    try:
        live_audio_poll(observe, engine.tick, device=device)
    except KeyboardInterrupt:
        print("\nStopped.")


def command_probe_audio(device, output_name: str) -> None:
    sink = MidoSink(output_name).open()

    def audible(event: TransportEvent) -> None:
        sink(event)
        print(f"\nAI {event.kind} note={event.pitch_midi} vel={event.velocity}")

    engine = EnsembleEngine(_core(), audible)
    engine.start()
    print("Audio-first closed loop running. Play into the microphone; pause to invite a response.")
    try:
        live_audio_poll(engine.ingest, engine.tick, device=device)
    except KeyboardInterrupt:
        pass
    finally:
        engine.stop()
        sink.close()
        print("\nStopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="RealSolo live ensemble runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ports")
    assets = sub.add_parser("install-assets")
    assets.add_argument("--profile", choices=PROFILES, default="full")
    use_assets = sub.add_parser("use-assets")
    use_assets.add_argument("--profile", choices=PROFILES, required=True)
    stage1 = sub.add_parser("stage1")
    stage1.add_argument("--host", default="127.0.0.1")
    stage1.add_argument("--port", type=int, default=8765)
    stage1.add_argument("--asset-profile", choices=PROFILES, default=None)
    research = sub.add_parser("research-listener")
    research.add_argument("--host", default="127.0.0.1")
    research.add_argument("--port", type=int, default=8771)

    mm = sub.add_parser("monitor-midi")
    mm.add_argument("--input", required=True)

    ma = sub.add_parser("monitor-audio")
    ma.add_argument("--device", default=None)

    pa = sub.add_parser("probe-audio")
    pa.add_argument("--device", default=None)
    pa.add_argument("--output", required=True)

    args = parser.parse_args()
    if args.command == "ports":
        command_ports()
    elif args.command == "install-assets":
        install_assets(args.profile)
    elif args.command == "use-assets":
        activate_profile(args.profile)
    elif args.command == "stage1":
        if args.asset_profile:
            activate_profile(args.asset_profile)
        run_stage1_web(args.host, args.port)
    elif args.command == "research-listener":
        run_research_web(args.host, args.port)
    elif args.command == "monitor-midi":
        command_monitor_midi(args.input)
    elif args.command == "monitor-audio":
        device = int(args.device) if args.device is not None and str(args.device).isdigit() else args.device
        command_monitor_audio(device)
    else:
        device = int(args.device) if args.device is not None and str(args.device).isdigit() else args.device
        command_probe_audio(device, args.output)


if __name__ == "__main__":
    main()
