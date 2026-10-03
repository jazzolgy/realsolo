"""Optional local learned-audio model service backend.

This lets the research listener use production instrument/role models without
coupling the core app to one ML framework or model package. The endpoint is
restricted to localhost by default so captured audio is not sent to a remote
service accidentally.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class ModelServiceError(RuntimeError):
    pass


@dataclass
class LocalInstrumentModelServiceBackend:
    endpoint: str = "http://127.0.0.1:8788/v1/predict"
    timeout_s: float = 3.0
    allow_remote: bool = False

    def __post_init__(self) -> None:
        parsed=urlparse(self.endpoint)
        if parsed.scheme not in {"http","https"}:
            raise ValueError("model service endpoint must be http(s)")
        host=(parsed.hostname or "").lower()
        if not self.allow_remote and host not in {"127.0.0.1","localhost","::1"}:
            raise ValueError("remote model service disabled; use localhost or explicitly allow_remote")

    def predict(
        self,
        samples,
        *,
        sample_rate: int,
    ) -> tuple[Mapping[str,float], Mapping[str,float], Mapping[str,float]]:
        try:
            import numpy as np
        except ImportError as exc:
            raise ModelServiceError('Install audio support with: pip install -e ".[audio]"') from exc
        x=np.asarray(samples,dtype="<f4").reshape(-1)
        payload=x.tobytes()
        req=Request(
            self.endpoint,
            data=payload,
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
            raise ModelServiceError(f"local model service request failed: {exc}") from exc
        if not isinstance(data,dict):
            raise ModelServiceError("model service returned non-object JSON")
        instruments=data.get("instrument_probabilities",{})
        roles=data.get("role_probabilities",{})
        confidence=data.get("confidence_fields",{})
        if not isinstance(instruments,dict) or not isinstance(roles,dict) or not isinstance(confidence,dict):
            raise ModelServiceError("model service probability fields must be JSON objects")
        return instruments,roles,confidence
