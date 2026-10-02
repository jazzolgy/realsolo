from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import urllib.request
import zipfile

ASSET_ROOT = Path(
    os.environ.get("REALSOLO_ASSET_ROOT", Path.home() / ".cache" / "realsolo" / "assets")
)

ASSETS = {
    "meatbass": {
        "url": "https://github.com/sfzinstruments/karoryfer.meatbass/releases/download/v1.001/Karoryfer.Meatbass.v1.001.zip",
        "sha256": None,
        "license": "CC0-1.0",
    },
    "virtuosity_drums": {
        "url": "https://github.com/sfzinstruments/virtuosity_drums/releases/download/v0.925/Virtuosity_Drums_v0.925.zip",
        "sha256": "c6c5d0fe11a394e94be3146a950c3377ec102cb57d189d5a23cec26183d1963a",
        "license": "CC0-1.0",
    },
}


def _download(url: str, target: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "RealSolo/asset-installer"})
    with urllib.request.urlopen(req) as src, target.open("wb") as dst:
        shutil.copyfileobj(src, dst)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_one(root: Path, suffix: str) -> Path:
    matches = [p for p in root.rglob("*") if p.as_posix().endswith(suffix)]
    if not matches:
        raise FileNotFoundError(suffix)
    return matches[0]


def _parse_simple_sfz(path: Path) -> list[dict]:
    """Parse the subset needed by RealSolo's approved CC0 packs.

    Supports group inheritance plus region sample/key/velocity/round-robin fields.
    Includes are intentionally not followed here; callers point at concrete map files.
    """
    regions: list[dict] = []
    group: dict[str, str] = {}
    current: dict[str, str] | None = None

    token_re = re.compile(r"([A-Za-z0-9_]+)=([^\s]+)")
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue
        if line.startswith("<group>"):
            group = {}
            current = None
            line = line[len("<group>"):].strip()
        elif line.startswith("<region>"):
            current = dict(group)
            regions.append(current)
            line = line[len("<region>"):].strip()

        for key, value in token_re.findall(line):
            if current is not None:
                current[key] = value
            else:
                group[key] = value

    out: list[dict] = []
    for i, r in enumerate(regions):
        sample = r.get("sample")
        if not sample:
            continue
        normalized = sample.replace("\\", "/")
        sample_path = (path.parent / normalized).resolve()
        out.append(
            {
                "sample_path": str(sample_path),
                "lokey": int(r.get("lokey", r.get("key", 0))),
                "hikey": int(r.get("hikey", r.get("key", 127))),
                "lovel": int(r.get("lovel", 1)),
                "hivel": int(r.get("hivel", 127)),
                "pitch_keycenter": int(r.get("pitch_keycenter", r.get("key", 60))),
                "rr": int(r.get("seq_position", i + 1)),
            }
        )
    return out


def _rel(root: Path, path: str) -> str:
    return Path(path).resolve().relative_to(root.resolve()).as_posix()


def build_manifest(root: Path) -> dict:
    meat = _find_one(root / "meatbass", "Programs/pizz_basic.sfz")
    bass_regions = _parse_simple_sfz(meat)

    drum_root = root / "virtuosity_drums"
    drum_maps = {
        "ride": "Programs/mappings/room/ride_ride_map.sfz",
        "hat_closed": "Programs/mappings/room/hh_closed_map.sfz",
        "kick": "Programs/mappings/room/kick_snon_map.sfz",
        "snare": "Programs/mappings/room/snare_center_map.sfz",
    }
    drums: dict[str, list[dict]] = {}
    for articulation, suffix in drum_maps.items():
        path = _find_one(drum_root, suffix)
        rows = _parse_simple_sfz(path)
        drums[articulation] = [
            {
                **{k: v for k, v in row.items() if k != "sample_path"},
                "sample": _rel(root, row["sample_path"]),
            }
            for row in rows
        ]

    bass = [
        {
            **{k: v for k, v in row.items() if k != "sample_path"},
            "sample": _rel(root, row["sample_path"]),
        }
        for row in bass_regions
    ]

    return {
        "version": 1,
        "packs": {
            "bass": {
                "id": "karoryfer_meatbass",
                "license": "CC0-1.0",
                "regions": bass,
            },
            "drums": {
                "id": "virtuosity_drums",
                "license": "CC0-1.0",
                "articulations": drums,
                "gm_map": {"51": "ride", "42": "hat_closed", "36": "kick", "38": "snare"},
            },
        },
    }


def install_assets(selected: tuple[str, ...] = ("meatbass", "virtuosity_drums")) -> Path:
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="realsolo-assets-") as tmp:
        tmp_path = Path(tmp)
        for asset_id in selected:
            spec = ASSETS[asset_id]
            dest = ASSET_ROOT / asset_id
            if dest.exists() and any(dest.iterdir()):
                print(f"{asset_id}: already installed")
                continue
            archive = tmp_path / f"{asset_id}.zip"
            print(f"{asset_id}: downloading...")
            _download(spec["url"], archive)
            if spec["sha256"] and _sha256(archive) != spec["sha256"]:
                raise RuntimeError(f"{asset_id}: SHA-256 mismatch")
            dest.mkdir(parents=True, exist_ok=True)
            print(f"{asset_id}: extracting...")
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(dest)

    manifest = build_manifest(ASSET_ROOT)
    manifest_path = ASSET_ROOT / "realsolo_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"RealSolo sample manifest: {manifest_path}")
    return manifest_path
