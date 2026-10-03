"""Raw RealChord / iReal playlist ingestion for the shared corpus.

Raw chart strings are preserved losslessly.  Structural parsing into
RealChordSong measures/chords is intentionally a separate stage so parser
improvements never destroy source provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import re
from urllib.parse import unquote


REALCHORD_1350_SOURCE_FILENAME = "Jazz 1350.html"
REALCHORD_1350_EXPECTED_COUNT = 1350


@dataclass(frozen=True)
class RealChordRawSong:
    realchord_id: str
    source_index: int
    title: str
    composer: str
    style: str
    key: str
    raw_chart: str
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.source_index < 1:
            raise ValueError("source_index must be 1-based")
        if not self.realchord_id:
            raise ValueError("realchord_id is required")
        if not self.title.strip():
            raise ValueError("title is required")


def parse_realchord_playlist_html(text: str) -> tuple[RealChordRawSong, ...]:
    """Parse the playlist envelope and preserve each raw chart payload.

    Stable ids are source-order ids.  This stage does not claim that the raw
    iReal chart encoding has already been normalized into bars/repeats/chords.
    """
    match = re.search(r'href=["\']irealb://([^"\']+)["\']', text, re.I)
    if match is None:
        raise ValueError("no irealb:// playlist payload found")
    payload = unquote(unescape(match.group(1)))

    records: list[RealChordRawSong] = []
    tokens = payload.split("===")
    for source_index, token in enumerate(tokens, 1):
        if not token.strip():
            continue
        fields = token.split("=")
        if len(fields) < 7:
            # Modern playlist exports append the playlist display name after
            # the final === delimiter. It is not a song record.
            if source_index == len(tokens):
                continue
            raise ValueError(
                f"malformed RealChord item at source index {source_index}"
            )
        item = RealChordRawSong(
            realchord_id=str(source_index),
            source_index=source_index,
            title=fields[0],
            composer=fields[1],
            style=fields[3],
            key=fields[4],
            raw_chart=fields[6],
            provenance=(
                "realchord:1350",
                REALCHORD_1350_SOURCE_FILENAME,
                f"source_index:{source_index}",
            ),
        )
        item.validate()
        records.append(item)
    return tuple(records)


def find_realchord_song(
    songs: tuple[RealChordRawSong, ...],
    title: str,
) -> RealChordRawSong:
    needle = " ".join(title.casefold().split())
    exact = [
        song for song in songs
        if " ".join(song.title.casefold().split()) == needle
    ]
    if len(exact) != 1:
        raise LookupError(
            f"expected exactly one RealChord title match for {title!r}; "
            f"found {len(exact)}"
        )
    return exact[0]
