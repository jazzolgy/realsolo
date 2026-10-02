from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import tarfile
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
GITHUB_RAW = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"

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


def _download_raw(repo: str, remote_path: str, local_path: Path, *, ref: str = "master") -> None:
    if local_path.exists() and local_path.stat().st_size > 0:
        return
    _download(GITHUB_RAW.format(repo=repo, ref=ref, path=remote_path), local_path)


def _read_raw_text(repo: str, remote_path: str, *, ref: str = "master") -> str:
    url = GITHUB_RAW.format(repo=repo, ref=ref, path=remote_path)
    req = urllib.request.Request(url, headers={"User-Agent": "RealSolo/asset-installer"})
    with urllib.request.urlopen(req) as src:
        return src.read().decode("utf-8")


def _parse_osiris_mapping(text: str, *, lovel: int, hivel: int) -> list[dict]:
    regions: list[dict] = []
    current: dict[str, str] | None = None
    token_re = re.compile(r"([A-Za-z0-9_]+)=([^\s]+)")
    for raw in text.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue
        if line.startswith("<region>"):
            current = {}
            regions.append(current)
            line = line[len("<region>"):].strip()
        if current is None:
            continue
        for key, value in token_re.findall(line):
            current[key] = value

    out = []
    for row in regions:
        sample = row.get("sample")
        if not sample:
            continue
        lokey = int(row.get("lokey", row.get("key", 0)))
        hikey = int(row.get("hikey", row.get("key", 127)))
        center = int(row.get("pitch_keycenter", (lokey + hikey) // 2))
        # Osiris mapping is included from Programs/*.sfz, so ../UC/... points
        # to the repository-root UC/... folder.
        remote = sample.replace("\\", "/")
        while remote.startswith("../"):
            remote = remote[3:]
        out.append({
            "remote": remote,
            "lokey": lokey,
            "hikey": hikey,
            "lovel": lovel,
            "hivel": hivel,
            "pitch_keycenter": center,
            "rr": 1,
        })
    return out


def _thin_regions(rows: list[dict], target: int) -> list[dict]:
    if target >= len(rows):
        return rows
    if target <= 1:
        return [rows[len(rows) // 2]]
    indexes = sorted({round(i * (len(rows) - 1) / (target - 1)) for i in range(target)})
    selected = [rows[i] for i in indexes]
    for i, row in enumerate(selected):
        prev_center = selected[i - 1]["pitch_keycenter"] if i else 20
        next_center = selected[i + 1]["pitch_keycenter"] if i + 1 < len(selected) else 109
        row = dict(row)
        row["lokey"] = 21 if i == 0 else (prev_center + row["pitch_keycenter"]) // 2 + 1
        row["hikey"] = 108 if i + 1 == len(selected) else (row["pitch_keycenter"] + next_center) // 2
        selected[i] = row
    return selected


def _osiris_regions(profile: str) -> list[dict]:
    paths = (
        ("Programs/modules/mappings/uc_micb_vl1_map.sfz", 1, 63),
        ("Programs/modules/mappings/uc_micb_vl2_map.sfz", 64, 127),
    )
    layers = [
        _parse_osiris_mapping(
            _read_raw_text("sfzinstruments/Osiris_Piano", path, ref="main"),
            lovel=lo,
            hivel=hi,
        )
        for path, lo, hi in paths
    ]
    if profile == "full":
        return layers[0] + layers[1]
    if profile == "lite":
        return _thin_regions(layers[0], 16) + _thin_regions(layers[1], 16)
    # Mini favors one medium/strong layer and sparse anchors.
    mini = _thin_regions(layers[1], 8)
    return [{**row, "lovel": 1, "hivel": 127} for row in mini]


def _install_osiris(profile: str) -> list[dict]:
    rows = _osiris_regions(profile)
    root = ASSET_ROOT / profile / "osiris_piano"
    for row in rows:
        remote = row["remote"]
        local = root / Path(remote).name
        _download_raw(
            "sfzinstruments/Osiris_Piano",
            remote,
            local,
            ref="main",
        )
    return [
        {
            **{k: v for k, v in row.items() if k != "remote"},
            "sample": f"{profile}/osiris_piano/{Path(row['remote']).name}",
        }
        for row in rows
    ]



_FREEPATS_TENOR = {
    "full": "https://freepats.zenvoid.org/Reed/TenorSaxophone/TenorSaxophone-SFZ%2BFLAC-20200717.tar.gz",
    "lite": "https://freepats.zenvoid.org/Reed/TenorSaxophone/TenorSaxophone-small-SFZ%2BFLAC-20200717.tar.gz",
    "mini": "https://freepats.zenvoid.org/Reed/TenorSaxophone/TenorSaxophone-small-SFZ%2BFLAC-20200717.tar.gz",
}

_TRUMPET_ANCHORS = {
    "F2": 41, "A2": 45, "C3": 48, "Ds3": 51, "F3": 53,
    "G3": 55, "As3": 58, "D4": 62, "F4": 65, "A4": 69, "C5": 72,
}


def _freepats_tenor_regions(profile: str) -> list[dict]:
    url = _FREEPATS_TENOR[profile]
    with tempfile.TemporaryDirectory(prefix="realsolo-tenor-") as td:
        temp = Path(td)
        archive = temp / "tenor.tar.gz"
        _download(url, archive)
        with tarfile.open(archive, "r:gz") as tf:
            tf.extractall(temp / "extract")
        sfzs = list((temp / "extract").rglob("*.sfz"))
        if not sfzs:
            raise RuntimeError("FreePats tenor sax archive contains no SFZ mapping")
        sfz = max(
            sfzs,
            key=lambda p: (
                "tenor" in p.name.lower(),
                "sax" in p.name.lower(),
                p.stat().st_size,
            ),
        )
        rows = _parse_simple_sfz(sfz)
        if profile == "mini":
            rows = _thin_regions(rows, min(8, len(rows)))

        root = ASSET_ROOT / profile / "freepats_tenor_sax"
        normalized: list[dict] = []
        for i, row in enumerate(rows):
            source = Path(row["sample_path"])
            if not source.is_file():
                continue
            local_name = f"{i:03d}_{source.name}"
            target = root / local_name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            normalized.append({
                **{k: v for k, v in row.items() if k != "sample_path"},
                "sample": f"{profile}/freepats_tenor_sax/{local_name}",
            })
        if not normalized:
            raise RuntimeError("FreePats tenor sax mapping resolved no audio samples")
        return normalized


def _trumpet_filename(family: str, note: str, velocity: int, rr: int = 1) -> str:
    display = note.replace("Ds", "D#").replace("As", "A#")
    return f"Sum_SHTrumpet_{family}_{display}_v{velocity}_rr{rr}.wav"


def _trumpet_profile_spec(profile: str) -> dict[str, tuple[tuple[str, ...], tuple[int, ...], tuple[int, ...]]]:
    if profile == "full":
        return {
            "sustain": (("F2","A2","C3","Ds3","G3","As3","D4","F4","A4","C5"), (1,3), (1,)),
            "vibrato": (("F2","A2","C3","Ds3","F3","G3","As3","D4","F4","A4","C5"), (1,2), (1,)),
            "short": (("F2","A2","C3","Ds3","F3","G3","As3","D4","F4","A4","C5"), (1,2,3), (1,2)),
        }
    if profile == "lite":
        anchors = ("F2","C3","G3","D4","A4","C5")
        return {
            "sustain": (anchors, (1,3), (1,)),
            "vibrato": (anchors, (1,2), (1,)),
            "short": (anchors, (2,), (1,2)),
        }
    anchors = ("A2","C3","G3","D4","A4")
    return {
        "sustain": (anchors, (3,), (1,)),
        "short": (anchors, (2,), (1,)),
    }


def _trumpet_remote_family(family: str) -> str:
    return {"sustain": "sus", "vibrato": "susvib", "short": "stac"}[family]


def _install_trumpet(profile: str) -> dict[str, list[dict]]:
    root = ASSET_ROOT / profile / "vsco_trumpet"
    articulations: dict[str, list[dict]] = {}
    for family, (notes, velocities, rrs) in _trumpet_profile_spec(profile).items():
        remote_family = _trumpet_remote_family(family)
        centers = [(note, _TRUMPET_ANCHORS[note]) for note in notes]
        regions: list[dict] = []
        for idx, (note, center) in enumerate(centers):
            previous = centers[idx - 1][1] if idx else center - 5
            following = centers[idx + 1][1] if idx + 1 < len(centers) else center + 5
            lokey = max(34, center - 3 if idx == 0 else (previous + center) // 2 + 1)
            hikey = min(76, center + 3 if idx + 1 == len(centers) else (center + following) // 2)
            for vi, vel in enumerate(velocities):
                lovel = 1 if vi == 0 else int(round(1 + vi * 127 / len(velocities)))
                hivel = 127 if vi + 1 == len(velocities) else int(round((vi + 1) * 127 / len(velocities)))
                for rr in rrs:
                    filename = _trumpet_filename(remote_family, note, vel, rr)
                    remote = f"Brass/Trumpet/{remote_family}/{filename}"
                    target = root / filename
                    _download_raw("sgossner/VSCO-2-CE", remote, target, ref="master")
                    regions.append({
                        "sample": f"{profile}/vsco_trumpet/{filename}",
                        "lokey": lokey, "hikey": hikey,
                        "lovel": lovel, "hivel": hivel,
                        "pitch_keycenter": center, "rr": rr,
                    })
        articulations[family] = regions
    return articulations


def _install_solo_assets(profile: str) -> tuple[dict, dict]:
    sax = {
        "id": f"freepats_tenor_sax_{profile}",
        "instrument": "tenor_sax",
        "license": "CC0-1.0",
        "articulations": {"sustain": _freepats_tenor_regions(profile)},
    }
    trumpet = {
        "id": f"vsco2ce_trumpet_{profile}",
        "instrument": "trumpet",
        "license": "CC0-1.0",
        "articulations": _install_trumpet(profile),
    }
    return sax, trumpet


def _ranges(anchors: dict[str, int], low_floor: int = 21, high_ceiling: int = 55):
    items = list(anchors.items())
    out = []
    for i, (name, center) in enumerate(items):
        low = low_floor if i == 0 else (items[i - 1][1] + center) // 2 + 1
        high = high_ceiling if i == len(items) - 1 else (center + items[i + 1][1]) // 2
        out.append((name, center, low, high))
    return out


def _sampled_manifest(profile: str, anchors: dict[str, int], layers, rrs, drum_files, piano_regions=None, solo_sax=None, solo_trumpet=None) -> dict:
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
            "solo_sax": solo_sax or {},
            "solo_trumpet": solo_trumpet or {},
            "piano": {
                "id": f"osiris_piano_{profile}",
                "license": "CC0-1.0",
                "regions": list(piano_regions or ()),
            },
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

    piano_regions = _install_osiris(profile)
    solo_sax, solo_trumpet = _install_solo_assets(profile)
    manifest = _sampled_manifest(
        profile, anchors, layers, rrs, drum_files, piano_regions,
        solo_sax, solo_trumpet
    )
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
    piano_regions = _install_osiris("full")
    solo_sax, solo_trumpet = _install_solo_assets("full")
    manifest["packs"]["solo_sax"] = solo_sax
    manifest["packs"]["solo_trumpet"] = solo_trumpet
    manifest["packs"]["piano"] = {
        "id": "osiris_piano_full",
        "license": "CC0-1.0",
        "regions": piano_regions,
    }
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
