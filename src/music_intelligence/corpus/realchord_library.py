"""Shared in-process RealChord Hub.

All consumers resolve songs through the same stable realchord_id rather than
maintaining independent copies of chord/form state.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence

from .realchord import RealChordSong, song_from_normalized_record


@dataclass(frozen=True)
class RealChordLibrary:
    songs: tuple[RealChordSong, ...]

    def __post_init__(self) -> None:
        ids = [song.realchord_id for song in self.songs]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate realchord_id in library")
        for song in self.songs:
            song.validate()

    def get(self, realchord_id: str) -> RealChordSong:
        for song in self.songs:
            if song.realchord_id == realchord_id:
                return song
        raise KeyError(realchord_id)

    def find_title(self, title: str) -> tuple[RealChordSong, ...]:
        wanted = title.strip().casefold()
        return tuple(song for song in self.songs if song.title.strip().casefold() == wanted)

    def __len__(self) -> int:
        return len(self.songs)


def library_from_normalized_corpus(record: Mapping[str, object]) -> RealChordLibrary:
    raw_songs = record.get("songs", ())
    if not isinstance(raw_songs, Sequence):
        raise TypeError("corpus songs must be a sequence")
    songs = []
    for item in raw_songs:
        if not isinstance(item, Mapping):
            raise TypeError("each corpus song must be a mapping")
        songs.append(song_from_normalized_record(item))
    return RealChordLibrary(tuple(songs))


def load_realchord_library(path: str | Path) -> RealChordLibrary:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise TypeError("RealChord corpus root must be a JSON object")
    return library_from_normalized_corpus(payload)
