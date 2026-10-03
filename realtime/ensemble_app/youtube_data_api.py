"""Concrete YouTube Data API v3 search adapter for research-source discovery.

Only metadata is retrieved. Media bytes are never downloaded or exposed here.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import os
import re
from typing import Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .youtube_research_provider import YouTubeSearchQuery, YouTubeSearchResult


_API_ROOT="https://www.googleapis.com/youtube/v3"
_DURATION_RE=re.compile(
    r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+(?:\.\d+)?)S)?)?$"
)


class YouTubeDataAPIError(RuntimeError):
    pass


def parse_iso8601_duration_seconds(value: str | None) -> float | None:
    if not value:
        return None
    match=_DURATION_RE.match(value)
    if not match:
        return None
    days=float(match.group("days") or 0)
    hours=float(match.group("hours") or 0)
    minutes=float(match.group("minutes") or 0)
    seconds=float(match.group("seconds") or 0)
    return days*86400+hours*3600+minutes*60+seconds


def _tokenize(value: str) -> set[str]:
    return {x for x in re.findall(r"[a-z0-9]+", value.lower()) if len(x)>1}


def _identity_confidence(artist: str, *text: str) -> float:
    if not artist.strip():
        return 0.82  # open discovery: identity is intentionally unresolved
    wanted=_tokenize(artist)
    observed=_tokenize(" ".join(text))
    if not wanted:
        return 0.65
    overlap=len(wanted & observed)/len(wanted)
    if overlap>=1.0:
        return 0.96
    if overlap>=0.5:
        return 0.82
    if overlap>0:
        return 0.68
    return 0.35


def _audio_suitability(duration_s: float | None, title: str) -> float:
    if duration_s is None:
        base=0.58
    elif 120 <= duration_s <= 5400:
        base=0.88
    elif 45 <= duration_s <= 10800:
        base=0.72
    else:
        base=0.48
    lowered=title.lower()
    if any(word in lowered for word in ("interview","lesson","reaction","review","analysis")):
        base-=0.22
    if any(word in lowered for word in ("live","concert","trio","quartet","quintet","full album","session")):
        base+=0.08
    return max(0.0,min(1.0,base))


def _source_reliability(channel: str, title: str) -> float:
    # Provider metadata is source-selection evidence only. This is intentionally
    # conservative and must never be promoted into musical evidence.
    value=0.62
    if channel.strip():
        value+=0.08
    if title.strip():
        value+=0.05
    return min(0.82,value)


@dataclass
class YouTubeDataAPIProvider:
    api_key: str
    timeout_s: float = 15.0
    region_code: str | None = None
    relevance_language: str | None = None

    @classmethod
    def from_environment(cls) -> "YouTubeDataAPIProvider":
        key=os.environ.get("YOUTUBE_API_KEY","").strip()
        if not key:
            raise YouTubeDataAPIError(
                "YOUTUBE_API_KEY is not configured. Create a YouTube Data API v3 key and set it in the environment."
            )
        return cls(
            api_key=key,
            region_code=os.environ.get("REALSOLO_YOUTUBE_REGION") or None,
            relevance_language=os.environ.get("REALSOLO_YOUTUBE_LANGUAGE") or None,
        )

    def _get(self, path: str, params: dict[str,object]) -> dict:
        query={k:v for k,v in params.items() if v is not None}
        query["key"]=self.api_key
        url=f"{_API_ROOT}/{path}?{urlencode(query)}"
        request=Request(url,headers={"Accept":"application/json","User-Agent":"RealSolo-Research/0.2"})
        try:
            with urlopen(request,timeout=self.timeout_s) as response:
                payload=json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise YouTubeDataAPIError(f"YouTube API request failed: {exc}") from exc
        if not isinstance(payload,dict):
            raise YouTubeDataAPIError("unexpected YouTube API response")
        return payload

    def search_for_artist(
        self,
        query: YouTubeSearchQuery,
        *,
        artist: str = "",
    ) -> tuple[YouTubeSearchResult,...]:
        query.validate()
        search_payload=self._get("search",{
            "part":"snippet",
            "type":"video",
            "q":query.terms,
            "maxResults":query.max_results,
            "videoEmbeddable":"true",
            "videoSyndicated":"true",
            "regionCode":self.region_code,
            "relevanceLanguage":self.relevance_language,
        })
        ids=[
            str(item.get("id",{}).get("videoId",""))
            for item in search_payload.get("items",[])
            if isinstance(item,dict) and item.get("id",{}).get("videoId")
        ]
        if not ids:
            return ()
        detail_payload=self._get("videos",{
            "part":"snippet,contentDetails,status",
            "id":",".join(ids),
            "maxResults":len(ids),
        })
        details={str(item.get("id","")):item for item in detail_payload.get("items",[]) if isinstance(item,dict)}
        out=[]
        for video_id in ids:
            item=details.get(video_id,{})
            snippet=item.get("snippet",{}) if isinstance(item,dict) else {}
            status=item.get("status",{}) if isinstance(item,dict) else {}
            content=item.get("contentDetails",{}) if isinstance(item,dict) else {}
            title=str(snippet.get("title",""))
            channel=str(snippet.get("channelTitle",""))
            description=str(snippet.get("description",""))
            duration=parse_iso8601_duration_seconds(str(content.get("duration","")) or None)
            embeddable=bool(status.get("embeddable",False))
            privacy=str(status.get("privacyStatus",""))
            upload=str(status.get("uploadStatus","processed"))
            playable=embeddable and privacy=="public" and upload=="processed"
            out.append(YouTubeSearchResult(
                video_id=video_id,
                title=title,
                channel_title=channel,
                duration_s=duration,
                embeddable=embeddable,
                playable=playable,
                identity_confidence=_identity_confidence(artist,title,channel,description),
                source_reliability=_source_reliability(channel,title),
                audio_suitability=_audio_suitability(duration,title),
                metadata={
                    "published_at":snippet.get("publishedAt"),
                    "channel_id":snippet.get("channelId"),
                    "provider_license":status.get("license"),
                    "privacy_status":privacy,
                    "upload_status":upload,
                },
            ))
        return tuple(out)

    def search(self, query: YouTubeSearchQuery) -> tuple[YouTubeSearchResult,...]:
        return self.search_for_artist(query,artist="")
