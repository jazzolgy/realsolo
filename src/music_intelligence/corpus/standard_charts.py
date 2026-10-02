"""Shared 100-standard chart corpus for every RealSolo player.

The chart corpus belongs to Core, not to any instrument workstream.

Source:
    Shanahan & Broze, iRealPro Corpus of Jazz Standards v1.0
    Zenodo DOI: 10.5281/zenodo.3546040
    License: CC BY 4.0

Raw source files are installed under REALSOLO_CORPUS_ROOT instead of copied into
instrument branches. Bass, piano, drums, sax, transcribe, and ensemble research
all resolve the same stable chart IDs.

This module intentionally stores a curated 100-title manifest and ingestion
logic. It does not contain melody, lyrics, or copied bass/solo lines.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import tempfile
import unicodedata
import urllib.request
import zipfile

from .registry import (
    CorpusAccess,
    CorpusItem,
    CorpusKind,
    CorpusRegistry,
    CorpusUse,
    RightsProfile,
    corpus_root_from_env,
)


IREALB_V1_DOI = "10.5281/zenodo.3546040"
IREALB_V1_URL = "https://zenodo.org/records/3546040"
IREALB_V1_ARCHIVE_URL = (
    "https://zenodo.org/records/3546040/files/shanahdt/irealb-v1.0.zip?download=1"
)
IREALB_V1_LICENSE = "CC BY 4.0"
IREALB_V1_DATASET_ID = "symbolic.irealb.v1"

ALL_PLAYER_INSTRUMENTS = frozenset({
    "bass",
    "piano",
    "drums",
    "sax",
    "soloist",
    "transcribe",
    "ensemble",
})

STANDARD_100_TITLES: tuple[str, ...] = (
    "A Foggy Day",
    "Afternoon In Paris",
    "Ain't Misbehavin'",
    "Airegin",
    "All Of Me",
    "All Of You",
    "All The Things You Are",
    "Alone Together",
    "Anthropology",
    "April In Paris",
    "Autumn Leaves",
    "Beautiful Love",
    "Bemsha Swing",
    "Bernie's Tune",
    "Billie's Bounce",
    "Blue Monk",
    "Blues For Alice",
    "Body And Soul",
    "But Beautiful",
    "But Not For Me",
    "Bye Bye Blackbird",
    "Cherokee",
    "Confirmation",
    "Cotton Tail",
    "Darn That Dream",
    "Days Of Wine And Roses",
    "Dear Old Stockholm",
    "Donna Lee",
    "Easy Living",
    "Embraceable You",
    "Four",
    "Gee Baby, Ain't I Good To You",
    "Giant Steps",
    "Groovin' High",
    "Honeysuckle Rose",
    "How High The Moon",
    "I Can't Get Started",
    "I Could Write A Book",
    "I Got Rhythm",
    "I Hear A Rhapsody",
    "I Love You",
    "I Mean You",
    "I Remember You",
    "I'll Remember April",
    "I'm Old Fashioned",
    "It Could Happen To You",
    "It's You Or No One",
    "Joy Spring",
    "Just Friends",
    "Lady Bird",
    "Like Someone In Love",
    "Love For Sale",
    "Lover Man",
    "Lullaby Of Birdland",
    "Mean To Me",
    "Misty",
    "Moonglow",
    "My Funny Valentine",
    "My One And Only Love",
    "My Romance",
    "Nardis",
    "Night And Day",
    "Oleo",
    "Out Of Nowhere",
    "Pennies From Heaven",
    "Rhythm-a-ning",
    "Round Midnight",
    "Satin Doll",
    "Scrapple From The Apple",
    "Softly, As In A Morning Sunrise",
    "Solar",
    "Stella By Starlight",
    "Straight No Chaser",
    "Summertime",
    "Take The A Train",
    "Tangerine",
    "Tea For Two",
    "There Is No Greater Love",
    "There Will Never Be Another You",
    "What Is This Thing Called Love",
    "What's New",
    "Whisper Not",
    "Yesterdays",
    "You Don't Know What Love Is",
    "You Stepped Out Of A Dream",
    "You'd Be So Nice To Come Home To",
    "On Green Dolphin Street",
    "Speak Low",
    "Star Eyes",
    "Tune Up",
    "Woody'n You",
    "Dolphin Dance",
    "Blue In Green",
    "Stablemates",
    "Moment's Notice",
    "Daahoud",
    "Along Came Betty",
    "Ceora",
    "Con Alma",
    "Doxy",
)


@dataclass(frozen=True)
class StandardChartInstallReport:
    installed_titles: tuple[str, ...]
    missing_titles: tuple[str, ...]
    destination: Path

    @property
    def complete(self) -> bool:
        return not self.missing_titles


def _normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.replace("’", "'").replace("–", "-").replace("—", "-")
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def _slug(value: str) -> str:
    return _normalize_title(value).replace(" ", "_")


def chart_item_id(title: str) -> str:
    return f"chart.standard100.{_slug(title)}"


def chart_relpath(title: str) -> str:
    return f"symbolic/irealb_v1_0/standard100/{_slug(title)}.krn"


def _source_rights() -> RightsProfile:
    return RightsProfile(
        source=IREALB_V1_URL,
        rights_holder="Daniel Shanahan; Yuri Broze",
        license=IREALB_V1_LICENSE,
        training_permission=True,
        research_permission=True,
        commercial_permission=True,
        redistribution_permission=True,
        notes=(
            "Dataset published on Zenodo under CC BY 4.0. Preserve attribution "
            "and provenance when redistributing or deriving chart data."
        ),
    )


def standard_100_corpus_items() -> tuple[CorpusItem, ...]:
    """Return one dataset record plus 100 stable shared chart records."""
    rights = _source_rights()
    parent = CorpusItem(
        item_id=IREALB_V1_DATASET_ID,
        kind=CorpusKind.MUSICAL_INTELLIGENCE,
        media_type="application/zip",
        title="iRealPro Corpus of Jazz Standards v1.0",
        artist_or_source="Daniel Shanahan; Yuri Broze",
        external_ref=IREALB_V1_URL,
        access=CorpusAccess.EXTERNAL_REFERENCE,
        uses=frozenset({
            CorpusUse.TRAINING,
            CorpusUse.RESEARCH,
            CorpusUse.REFERENCE,
            CorpusUse.EVALUATION,
            CorpusUse.REDISTRIBUTION,
        }),
        tags=frozenset({"jazz", "standard", "symbolic", "chord_chart", "shared_core"}),
        instruments=ALL_PLAYER_INSTRUMENTS,
        rights=rights,
        provenance=(f"doi:{IREALB_V1_DOI}", "irealb_corpus_v1.0"),
    )

    charts = tuple(
        CorpusItem(
            item_id=chart_item_id(title),
            kind=CorpusKind.MUSICAL_INTELLIGENCE,
            media_type="text/x-humdrum",
            title=title,
            artist_or_source="iRealPro Corpus of Jazz Standards v1.0",
            local_relpath=chart_relpath(title),
            access=CorpusAccess.LOCAL_PRIVATE,
            uses=frozenset({
                CorpusUse.TRAINING,
                CorpusUse.RESEARCH,
                CorpusUse.REFERENCE,
                CorpusUse.EVALUATION,
            }),
            tags=frozenset({
                "jazz",
                "standard",
                "symbolic",
                "chord_chart",
                "standard100",
                "shared_core",
            }),
            instruments=ALL_PLAYER_INSTRUMENTS,
            derived_from=(IREALB_V1_DATASET_ID,),
            rights=rights,
            provenance=(f"doi:{IREALB_V1_DOI}", "standard100_manifest_v1"),
            notes=(
                "One shared canonical chart source for all RealSolo players. "
                "Player-specific realizations must not edit this source."
            ),
        )
        for title in STANDARD_100_TITLES
    )
    return (parent,) + charts


def register_standard_100(registry: CorpusRegistry) -> None:
    for item in standard_100_corpus_items():
        registry.add(item)


def _extract_otl(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("!!!OTL:"):
            value = line.split(":", 1)[1].strip()
            return value or None
    return None


def _decode_chart(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("utf-8", data, 0, 1, "unable to decode chart")


def install_standard_100_from_archive(
    archive_path: str | Path,
    *,
    root: str | Path | None = None,
) -> StandardChartInstallReport:
    """Install the curated 100 raw charts from the licensed source archive.

    The caller supplies the official Zenodo archive. The function discovers
    Humdrum/Kern files by their !!!OTL title metadata and writes a canonical
    copy to the shared corpus root. This keeps every instrument on the same
    source chart while preserving the original raw chart text.
    """
    archive = Path(archive_path).expanduser().resolve()
    if not archive.is_file():
        raise FileNotFoundError(archive)

    base = Path(root).expanduser().resolve() if root is not None else corpus_root_from_env()
    destination = base / "symbolic" / "irealb_v1_0" / "standard100"
    destination.mkdir(parents=True, exist_ok=True)

    target_by_norm = {_normalize_title(t): t for t in STANDARD_100_TITLES}
    found: dict[str, bytes] = {}

    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            suffix = Path(info.filename).suffix.lower()
            if suffix not in {".krn", ".kern", ".txt", ".hum"}:
                continue
            raw = zf.read(info)
            text = _decode_chart(raw)
            title = _extract_otl(text)
            if title is None:
                title = Path(info.filename).stem
            canonical = target_by_norm.get(_normalize_title(title))
            if canonical is not None and canonical not in found:
                found[canonical] = raw

    for title, raw in found.items():
        (destination / f"{_slug(title)}.krn").write_bytes(raw)

    missing = tuple(title for title in STANDARD_100_TITLES if title not in found)
    installed = tuple(title for title in STANDARD_100_TITLES if title in found)
    return StandardChartInstallReport(installed, missing, destination)


def download_and_install_standard_100(
    *,
    root: str | Path | None = None,
    archive_url: str = IREALB_V1_ARCHIVE_URL,
) -> StandardChartInstallReport:
    """Download the official CC-BY archive and install the shared Standard 100.

    Network access belongs to installation/setup, never to realtime player
    decision logic. The downloaded archive is temporary; canonical raw chart
    files are preserved in the shared corpus root.
    """
    request = urllib.request.Request(
        archive_url,
        headers={"User-Agent": "RealSolo-Music-Intelligence/1.52"},
    )
    with tempfile.TemporaryDirectory(prefix="realsolo-standard100-") as tmp:
        archive = Path(tmp) / "irealb-v1.0.zip"
        with urllib.request.urlopen(request) as src, archive.open("wb") as dst:
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)
        return install_standard_100_from_archive(archive, root=root)
