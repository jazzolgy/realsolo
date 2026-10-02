"""v1.30 development-only performance audit."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
from .legend_style_core import CandidateEvent

@dataclass(frozen=True)
class AuditFinding:
    index: int
    severity: str
    code: str
    message: str

def audit_completed_phrase(events: Sequence[CandidateEvent]) -> tuple[AuditFinding,...]:
    out=[]
    for i,e in enumerate(events):
        if "routine_downbeat_long_tone" in e.tags:
            out.append(AuditFinding(i,"warning","routine_downbeat_hold",
                                    "long hold lacks structural/syncopated rationale"))
        if "exposed_maj7_natural11" in e.tags and not ({"passing","neighbor","enclosure","suspension"} & set(e.tags)):
            out.append(AuditFinding(i,"warning","maj7_natural11",
                                    "exposed natural 11 on maj7 needs contextual justification"))
        if "repeated_wide_leap" in e.tags:
            out.append(AuditFinding(i,"warning","leap_stack",
                                    "wide leap pressure accumulated inside phrase"))
    return tuple(out)
