#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNERSHIP = ROOT / "docs/ARCHITECTURE_OWNERSHIP.yaml"


def load_policy():
    return json.loads(OWNERSHIP.read_text(encoding="utf-8"))


def changed_paths(base: str) -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(line.strip() for line in result.stdout.splitlines() if line.strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--area", required=True)
    parser.add_argument("--base", default="origin/main")
    args = parser.parse_args()

    policy = load_policy()
    area = policy["areas"].get(args.area)
    if area is None:
        raise SystemExit(f"unknown architecture area: {args.area}")

    paths = changed_paths(args.base)
    forbidden = tuple(area.get("must_not_modify", ()))
    violations = [
        path for path in paths
        if any(fnmatch.fnmatch(path, pattern) for pattern in forbidden)
    ]

    print(f"Architecture Preflight: area={args.area} base={args.base}")
    print(f"changed files: {len(paths)}")
    if violations:
        print("boundary violations:")
        for path in violations:
            print(f"  - {path}")
        return 1

    contract = policy.get("contracts", {}).get("performance_evidence", {})
    print("boundary path check: OK")
    if contract:
        print(f"Performance Evidence: {contract.get('current_version')} @ {contract.get('path')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
