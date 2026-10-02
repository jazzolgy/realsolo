"""Score-time sequence assembly for one notation voice.

This layer converts selected rhythmic candidates into an explicit sequence of
notes/rests. It does not decide pitch spelling or instrument performance policy.
"""
from __future__ import annotations

from fractions import Fraction

from .notation import NotatedAtom, NotatedAtomKind, NotationCandidate, rest_for_gap


def assemble_monophonic_voice(
    candidates: tuple[NotationCandidate, ...],
    *,
    start: Fraction = Fraction(0),
    end: Fraction | None = None,
    insert_rests: bool = True,
) -> tuple[NotatedAtom, ...]:
    """Assemble non-overlapping selected candidates into one readable voice."""

    atoms: list[NotatedAtom] = []
    for candidate in candidates:
        candidate.validate()
        atoms.extend(candidate.atoms)

    atoms.sort(key=lambda a: (a.span.onset, a.span.offset, a.kind.value))
    out: list[NotatedAtom] = []
    cursor = start

    for atom in atoms:
        if atom.span.onset < cursor:
            raise ValueError("selected atoms overlap in monophonic voice")
        if insert_rests and atom.span.onset > cursor:
            rest = rest_for_gap(cursor, atom.span.onset)
            if rest is not None:
                out.append(rest)
        out.append(atom)
        cursor = atom.span.offset

    if end is not None:
        if end < cursor:
            raise ValueError("voice end precedes final atom")
        if insert_rests and end > cursor:
            rest = rest_for_gap(cursor, end)
            if rest is not None:
                out.append(rest)

    return tuple(out)
