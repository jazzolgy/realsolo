"""Ingest an iReal/RealChord playlist HTML into stable RealChord raw records.

The raw chart string is preserved losslessly. Structural normalization of bars,
sections, repeats and endings is a separate parser stage.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import re
from urllib.parse import unquote


@dataclass(frozen=True)
class RealChordRawSong:
    realchord_id: int
    title: str
    composer: str
    style: str
    key: str
    raw_chart: str

    def validate(self) -> None:
        if self.realchord_id <= 0:
            raise ValueError("realchord_id must be positive")
        if not self.title.strip():
            raise ValueError("title is required")


def parse_realchord_playlist_html(text: str) -> tuple[RealChordRawSong,...]:
    match=re.search(r'href=["\']irealb://([^"\']+)["\']',text,re.I)
    if match is None:
        raise ValueError("no irealb:// playlist payload found")
    payload=unquote(unescape(match.group(1)))
    records=[]
    for source_index,token in enumerate(payload.split("==="),1):
        if not token.strip():
            continue
        fields=token.split("=")
        if len(fields) < 7:
            raise ValueError(f"malformed RealChord item at source index {source_index}")
        item=RealChordRawSong(
            realchord_id=source_index,
            title=fields[0],
            composer=fields[1],
            style=fields[3],
            key=fields[4],
            raw_chart=fields[6],
        )
        item.validate()
        records.append(item)
    return tuple(records)
