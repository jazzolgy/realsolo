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
PROFILES = ("full", "lite", "mini")

FULL_ASSETS = {
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
GITHUB_RAW = "https://raw.githubusercontent.com/{repo}/master/{path}"

_LITE_BASS_ANCHORS = {
    "eb1": 27, "gb1": 30, "a1": 33, "c2": 36,
    "eb2": 39, "gb2": 42, "a2": 45, "c3": 48,
}
_LITE_BASS_LAYERS = (("vl2", 1, 80), ("vl4", 81, 127))
_LITE_BASS_RR = (1, 2)

_MINI_BASS_ANCHORS = {"gb1": 30, "c2": 36, "gb2": 42, "c3": 48}
_MINI_BASS_LAYERS = (("vl3", 1, 127),)
_MINI_BASS_RR = (1,)

_DRUM_LITE = {
    "ride": [
        (f"Samples/room/ride/room_ride_ride_vl{vl}_rr{rr}.flac", lo, hi, rr)
        for vl, lo, hi in ((1, 1, 42), (2, 43, 85), (3, 86, 127))
        for rr in (1, 2)
    ],
    "hat_closed": [
        (f"Samples/room/hh/room_hh_closed_vl{vl}_rr{rr}.flac", lo, hi, rr)
        for vl, lo, hi in ((1, 1, 31), (2, 32, 63), (3, 64, 95), (4, 96, 127))
        for rr in (1, 2)
    ],
    "kick": [
        (f"Samples/room/kick/room_kick_snon_vl{vl}_rr{rr}.flac", lo, hi, rr)
        for vl, lo, hi in ((1, 1, 31), (2, 32, 63), (3, 64, 95), (4, 96, 127))
        for rr in (1, 2)
    ],
    "snare": [
        ("Samples/room/snare/room_snare_center_vl8.flac", 1, 31, 1),
        ("Samples/room/snare/room_snare_center_vl18.flac", 32, 63, 1),
        ("Samples/room/snare/room_snare_center_vl28.flac", 64, 95, 1),
        ("Samples/room/snare/room_snare_center_vl36.flac", 96, 127, 1),
    ],
}
_DRUM_MINI = {
    "ride": [("Samples/room/ride/room_ride_ride_vl2_rr1.flac", 1, 127, 1)],
    "hat_closed": [("Samples/room/hh/room_hh_closed_vl3_rr1.flac", 1, 127, 1)],
    "kick": [("Samples/room/kick/room_kick_snon_vl3_rr1.flac", 1, 127, 1)],
    "snare": [("Samples/room/snare/room_snare_center_vl28.flac", 1, 127, 1)],
}


def _download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "RealSolo/asset-installer"})
    with urllib.request.urlopen(req) as src, target.open("wb") as dst:
        shutil.copyfileobj(src, dst)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _download_raw(repo: str, remote_path: str, local_path: Path) -> None:
    if local_path.exists() and local_path.stat().st_size > 0:
        return
    _download(GITHUB_RAW.format(repo=repo, path=remote_path), local_path)


def _ranges(anchors: dict[str, int], low_floor: int = 21, high_ceiling: int = 55):
    items = list(anchors.items())
    out = []
    for i, (name, center) in enumerate(items):
        low = low_floor if i == 0 else (items[i - 1][1] + center) // 2 + 1
        high = high_ceiling if i == len(items) - 1 else (center + items[i + 1][1]) // 2
        out.append((name, center, low, high))
    return out


def _sampled_manifest(profile: str, anchors: dict[str, int], layers, rrs, drum_files) -> dict:
    bass_regions = []
    for name, center, low, high in _ranges(anchors):
        for layer, lovel, hivel in layers:
            for rr in rrs:
                bass_regions.append({
                    "sample": f"{profile}/meatbass/{name}_{layer}_rr{rr}.wav",
                    "lokey": low, "hikey": high,
                    "lovel": lovel, "hivel": hivel,
                    "pitch_keycenter": center, "rr": rr,
                })
    drums = {}
    for art, files in drum_files.items():
        drums[art] = [
            {
                "sample": f"{profile}/virtuosity_drums/{Path(remote).name}",
                "lokey": 0, "hikey": 127,
                "lovel": lovel, "hivel": hivel,
                "pitch_keycenter": 60, "rr": rr,
            }
            for remote, lovel, hivel, rr in files
        ]
    return {
        "version": 3,
        "profile": profile,
        "packs": {
            "bass": {
                "id": f"karoryfer_meatbass_{profile}",
                "license": "CC0-1.0",
                "regions": bass_regions,
            },
            "drums": {
                "id": f"virtuosity_drums_{profile}",
                "license": "CC0-1.0",
                "articulations": drums,
                "gm_map": {"51": "ride", "42": "hat_closed", "36": "kick", "38": "snare"},
            },
        },
    }


def _install_sampled_profile(profile: str) -> Path:
    if profile == "lite":
        anchors, layers, rrs, drum_files = (
            _LITE_BASS_ANCHORS, _LITE_BASS_LAYERS, _LITE_BASS_RR, _DRUM_LITE
        )
    elif profile == "mini":
        anchors, layers, rrs, drum_files = (
            _MINI_BASS_ANCHORS, _MINI_BASS_LAYERS, _MINI_BASS_RR, _DRUM_MINI
        )
    else:
        raise ValueError(profile)

    print(f"Installing RealSolo {profile.title()} Test Pack...")
    bass_root = ASSET_ROOT / profile / "meatbass"
    drum_root = ASSET_ROOT / profile / "virtuosity_drums"

    for name in anchors:
        for layer, _, _ in layers:
            for rr in rrs:
                filename = f"{name}_{layer}_rr{rr}.wav"
                _download_raw(
                    "sfzinstruments/karoryfer.meatbass",
                    f"Samples/pizz/{filename}",
                    bass_root / filename,
                )

    seen = set()
    for files in drum_files.values():
        for remote, _, _, _ in files:
            if remote in seen:
                continue
            seen.add(remote)
            _download_raw(
                "sfzinstruments/virtuosity_drums",
                remote,
                drum_root / Path(remote).name,
            )

    manifest = _sampled_manifest(profile, anchors, layers, rrs, drum_files)
    path = ASSET_ROOT / f"realsolo_manifest_{profile}.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    size = sum(p.stat().st_size for p in (ASSET_ROOT / profile).rglob("*") if p.is_file())
    print(f"{profile.title()} pack installed: {size / 1024 / 1024:.1f} MB")
    activate_profile(profile)
    return path


def _find_one(root: Path, suffix: str) -> Path:
    matches = [p for p in root.rglob("*") if p.as_posix().endswith(suffix)]
    if not matches:
        raise FileNotFoundError(suffix)
    return matches[0]


def _parse_simple_sfz(path: Path) -> list[dict]:
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
            (current if current is not None else group)[key] = value

    out = []
    for i, r in enumerate(regions):
        sample = r.get("sample")
        if not sample:
            continue
        sample_path = (path.parent / sample.replace("\\", "/")).resolve()
        out.append({
            "sample_path": str(sample_path),
            "lokey": int(r.get("lokey", r.get("key", 0))),
            "hikey": int(r.get("hikey", r.get("key", 127))),
            "lovel": int(r.get("lovel", 1)),
            "hivel": int(r.get("hivel", 127)),
            "pitch_keycenter": int(r.get("pitch_keycenter", r.get("key", 60))),
            "rr": int(r.get("seq_position", i + 1)),
        })
    return out


def _rel(root: Path, path: str) -> str:
    return Path(path).resolve().relative_to(root.resolve()).as_posix()


def _build_full_manifest(root: Path) -> dict:
    meat = _find_one(root / "meatbass", "Programs/pizz_basic.sfz")
    bass_regions = _parse_simple_sfz(meat)
    drum_root = root / "virtuosity_drums"
    drum_maps = {
        "ride": "Programs/mappings/room/ride_ride_map.sfz",
        "hat_closed": "Programs/mappings/room/hh_closed_map.sfz",
        "kick": "Programs/mappings/room/kick_snon_map.sfz",
        "snare": "Programs/mappings/room/snare_center_map.sfz",
    }
    drums = {}
    for art, suffix in drum_maps.items():
        rows = _parse_simple_sfz(_find_one(drum_root, suffix))
        drums[art] = [
            {**{k: v for k, v in row.items() if k != "sample_path"}, "sample": _rel(root, row["sample_path"])}
            for row in rows
        ]
    bass = [
        {**{k: v for k, v in row.items() if k != "sample_path"}, "sample": _rel(root, row["sample_path"])}
        for row in bass_regions
    ]
    return {
        "version": 3,
        "profile": "full",
        "packs": {
            "bass": {"id": "karoryfer_meatbass", "license": "CC0-1.0", "regions": bass},
            "drums": {
                "id": "virtuosity_drums",
                "license": "CC0-1.0",
                "articulations": drums,
                "gm_map": {"51": "ride", "42": "hat_closed", "36": "kick", "38": "snare"},
            },
        },
    }


def install_full_assets() -> Path:
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="realsolo-assets-") as tmp:
        tmp_path = Path(tmp)
        for asset_id, spec in FULL_ASSETS.items():
            dest = ASSET_ROOT / asset_id
            if dest.exists() and any(dest.iterdir()):
                print(f"{asset_id}: already installed")
                continue
            archive = tmp_path / f"{asset_id}.zip"
            print(f"{asset_id}: downloading full pack...")
            _download(spec["url"], archive)
            if spec["sha256"] and _sha256(archive) != spec["sha256"]:
                raise RuntimeError(f"{asset_id}: SHA-256 mismatch")
            dest.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(dest)

    manifest = _build_full_manifest(ASSET_ROOT)
    path = ASSET_ROOT / "realsolo_manifest_full.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    activate_profile("full")
    return path


def install_assets(profile: str = "full") -> Path:
    if profile not in PROFILES:
        raise ValueError(f"unknown asset profile: {profile}")
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    if profile == "full":
        return install_full_assets()
    return _install_sampled_profile(profile)


def activate_profile(profile: str) -> Path:
    if profile not in PROFILES:
        raise ValueError(f"unknown asset profile: {profile}")
    source = ASSET_ROOT / f"realsolo_manifest_{profile}.json"
    if not source.exists():
        raise FileNotFoundError(
            f"{profile} asset profile is not installed. "
            f"Run: realsolo-ensemble install-assets --profile {profile}"
        )
    active = ASSET_ROOT / "realsolo_manifest.json"
    shutil.copyfile(source, active)
    print(f"Active RealSolo asset profile: {profile}")
    return active
