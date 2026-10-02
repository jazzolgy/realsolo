from __future__ import annotations

import argparse
import time

from music_intelligence.reasoning.online_improviser import OnlineMusicalEvaluator, PerformanceMemory

from .core_bridge import CoreImmediateBridge, DiagnosticResponseFactory
from .engine import EnsembleEngine
from .midi_io import MidoSink, list_ports, live_poll
from .models import TransportEvent


def _core() -> CoreImmediateBridge:
    return CoreImmediateBridge(
        factory=DiagnosticResponseFactory(),
        evaluator=OnlineMusicalEvaluator(),
        memory=PerformanceMemory(),
    )


def _print_state(state) -> None:
    bpm = f"{state.beat.tempo_bpm:6.1f}" if state.beat.tempo_bpm else "   ?  "
    phase = f"{state.beat.phase:.2f}" if state.beat.phase is not None else "?"
    print(
        f"rev={state.revision:05d} bpm={bpm} phase={phase} "
        f"notes={sorted(state.active_notes)} activity={state.human_activity:.2f} "
        f"phrase_end={state.phrase.phrase_end}",
        end="\r",
        flush=True,
    )


def command_ports() -> None:
    ins, outs = list_ports()
    print("MIDI inputs:")
    print("\n".join(f"  {x}" for x in ins) or "  (none)")
    print("MIDI outputs:")
    print("\n".join(f"  {x}" for x in outs) or "  (none)")


def command_monitor(input_name: str) -> None:
    engine = EnsembleEngine(_core(), lambda _: None)
    last_print = 0.0

    def show(obs):
        nonlocal last_print
        state = engine.ingest(obs)
        if time.monotonic() - last_print > 0.08:
            _print_state(state)
            last_print = time.monotonic()

    def tick(now):
        nonlocal last_print
        state = engine.tick(now)
        if state.phrase.phrase_end or now - last_print > 0.12:
            _print_state(state)
            last_print = now

    try:
        live_poll(input_name, show, tick)
    except KeyboardInterrupt:
        print("\nStopped.")


def command_probe(input_name: str, output_name: str) -> None:
    sink = MidoSink(output_name).open()

    def audible(event: TransportEvent) -> None:
        sink(event)
        print(f"\nAI {event.kind} note={event.pitch_midi} vel={event.velocity}")

    engine = EnsembleEngine(_core(), audible)
    engine.start()
    print("Closed-loop diagnostic probe running. Play phrases; pause to invite a response. Ctrl-C to stop.")
    try:
        live_poll(input_name, engine.ingest, engine.tick)
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
    monitor = sub.add_parser("monitor")
    monitor.add_argument("--input", required=True)
    probe = sub.add_parser("probe")
    probe.add_argument("--input", required=True)
    probe.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.command == "ports":
        command_ports()
    elif args.command == "monitor":
        command_monitor(args.input)
    else:
        command_probe(args.input, args.output)


if __name__ == "__main__":
    main()
