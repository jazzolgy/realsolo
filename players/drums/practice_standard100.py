"""CLI: practice AI Drummer on REALSOLO standard100 private corpus."""
from __future__ import annotations

import argparse

from music_intelligence.drums.standard100_practice import practice_standard100


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None, help="Override REALSOLO_CORPUS_ROOT")
    parser.add_argument("--passes", type=int, default=4)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()

    report = practice_standard100(
        args.root,
        passes=args.passes,
        write_report=not args.no_write,
    )
    print(f"files_discovered={report.files_discovered}")
    print(f"charts_loaded={report.charts_loaded}")
    print(f"songs_practiced={report.songs_practiced}")
    print(f"total_bars_practiced={report.total_bars_practiced}")
    print(f"total_decisions={report.total_decisions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
