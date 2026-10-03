"""Optional localhost source-separation service.

The service receives one Float32 mono window and returns in-memory Float32 stems.
It is intentionally local-only by default. RealSolo does not persist returned
source media; stems exist only long enough to produce analysis evidence.
"""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .source_separation import SeparatedStem


class SeparationServiceError(RuntimeError):
    pass


@dataclass
class LocalSourceSeparationServiceBackend:
    endpoint: str = "http://127.0.0.1:8789/v1/separate"
    timeout_s: float = 8.0
    allow_remote: bool = False

    def __post_init__(self) -> None:
        parsed=urlparse(self.endpoint)
        if parsed.scheme not in {"http","https"}:
            raise ValueError("separator endpoint must be http(s)")
        host=(parsed.hostname or "").lower()
        if not self.allow_remote and host not in {"127.0.0.1","localhost","::1"}:
            raise ValueError("remote separator disabled; use localhost or explicitly allow_remote")

    def separate(self,samples,*,sample_rate:int):
        try:
            import numpy as np
        except ImportError as exc:
            raise SeparationServiceError('Install audio support with: pip install -e ".[audio]"') from exc
        x=np.asarray(samples,dtype="<f4").reshape(-1)
        req=Request(
            self.endpoint,
            data=x.tobytes(),
            method="POST",
            headers={
                "Content-Type":"application/octet-stream",
                "X-RealSolo-Sample-Rate":str(sample_rate),
                "X-RealSolo-Sample-Format":"float32le-mono",
                "Accept":"application/json",
            },
        )
        try:
            with urlopen(req,timeout=self.timeout_s) as response:
                data=json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise SeparationServiceError(f"local separation service request failed: {exc}") from exc
        stems=data.get("stems",[]) if isinstance(data,dict) else []
        out=[]
        for item in stems if isinstance(stems,list) else []:
            if not isinstance(item,dict):
                continue
            encoded=item.get("samples_b64","")
            if not encoded:
                continue
            try:
                raw=base64.b64decode(encoded,validate=True)
                arr=np.frombuffer(raw,dtype="<f4").copy()
            except Exception:
                continue
            stem=SeparatedStem(
                stem_id=str(item.get("stem_id","")),
                samples=arr,
                sample_rate=int(item.get("sample_rate",sample_rate)),
                source_family=str(item.get("source_family","")),
                confidence=float(item.get("confidence",0.0)),
            )
            stem.validate()
            out.append(stem)
        return tuple(out)
