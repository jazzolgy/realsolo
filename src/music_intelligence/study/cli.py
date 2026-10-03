"""Command line entry point for the first runnable RealSolo study MVP."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from music_intelligence.learning.score_alignment import PerformancePhase

from .session import ManualFormClock,StudySession,parse_section_map


def build_parser()->argparse.ArgumentParser:
    p=argparse.ArgumentParser(
        prog="realsolo-study",
        description=(
            "Study a local audio source into compact Shared-Core evidence. "
            "Without explicit musical alignment, observations remain navigation-only."
        ),
    )
    p.add_argument("audio")
    p.add_argument("--source-id",required=True)
    p.add_argument("--output",default="study_evidence.jsonl")
    p.add_argument("--song")
    p.add_argument("--bpm",type=float)
    p.add_argument("--meter",default="4/4")
    p.add_argument("--form-bars",type=int)
    p.add_argument("--form-start-s",type=float,default=0.0)
    p.add_argument("--realchord-id",default="")
    p.add_argument("--score-source-id",default="")
    p.add_argument("--sections",default="")
    p.add_argument(
        "--phase",
        choices=[x.value for x in PerformancePhase],
        default=PerformancePhase.UNKNOWN.value,
    )
    p.add_argument("--start-s",type=float,default=0.0,help="source-audio offset to begin studying")
    p.add_argument("--window-s",type=float,default=2.0)
    p.add_argument("--hop-s",type=float,default=1.0)
    p.add_argument("--max-seconds",type=float)
    return p


def main(argv=None)->int:
    args=build_parser().parse_args(argv)
    clock=None
    if args.song or args.bpm or args.form_bars or args.realchord_id:
        if not args.song or not args.bpm:
            raise SystemExit("--song and --bpm are both required for aligned study")
        try:
            num,den=(int(x) for x in args.meter.split("/",1))
        except Exception as exc:
            raise SystemExit("--meter must look like 4/4 or 6/8") from exc
        clock=ManualFormClock(
            song_id=args.song,
            bpm=args.bpm,
            meter_numerator=num,
            meter_denominator=den,
            form_length_bars=args.form_bars,
            form_start_s=args.form_start_s,
            realchord_id=args.realchord_id,
            score_source_id=args.score_source_id,
            sections=parse_section_map(args.sections),
            performance_phase=PerformancePhase(args.phase),
        )
        clock.validate()

    session=StudySession(
        source_id=args.source_id,
        output_path=Path(args.output),
        form_clock=clock,
    )
    summary=session.run(
        args.audio,
        start_s=args.start_s,
        window_s=args.window_s,
        hop_s=args.hop_s,
        max_seconds=args.max_seconds,
    )
    print(json.dumps(summary.__dict__,ensure_ascii=False,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
