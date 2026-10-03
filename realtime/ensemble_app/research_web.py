"""Local controller for the Autonomous Research Listener.

YouTube discovery/embed orchestration lives here. Musical interpretation does
not: audio analysis and persisted musical coordinates cross canonical Shared
Core adapters.
"""
from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .autonomous_research_session import AutonomousResearchSession
from .research_audio_ingest import ResearchAudioIngestor
from .research_checkpoint import ResearchCheckpoint, default_research_state_root
from .youtube_data_api import YouTubeDataAPIError, YouTubeDataAPIProvider
from .youtube_research_provider import YouTubeSearchQuery, youtube_embed_url


WEB_ROOT=Path(__file__).with_name("web")
DEFAULT_BOOTSTRAP_QUERY="jazz live performance full concert"


class ResearchRuntime:
    def __init__(self) -> None:
        self.session=AutonomousResearchSession()
        self.state_root=default_research_state_root()
        self.checkpoint_path=self.state_root/"listener_checkpoint.json"
        self.checkpoint=ResearchCheckpoint.load(self.checkpoint_path)
        self.checkpoint.restore_session(self.session)
        self.ingestor=ResearchAudioIngestor(
            evidence_root=self.state_root/"evidence",
        )
        self.last_query=self.checkpoint.last_query
        self.last_artist=self.checkpoint.last_artist

    def configured(self) -> bool:
        return bool(os.environ.get("YOUTUBE_API_KEY","").strip())

    def save(self) -> None:
        ResearchCheckpoint.from_session(
            self.session,
            last_query=self.last_query,
            last_artist=self.last_artist,
        ).save(self.checkpoint_path)

    def search(self,terms: str,artist: str="",max_results: int=24) -> int:
        provider=YouTubeDataAPIProvider.from_environment()
        query=YouTubeSearchQuery(terms=terms,max_results=max_results)
        results=provider.search_for_artist(query,artist=artist)
        candidates=tuple(
            x.to_candidate(
                artist=artist or "open-discovery",
                coverage_gap_score=.65,
            )
            for x in results
        )
        self.session.replace_candidates(candidates)
        self.last_query=terms
        self.last_artist=artist
        self.save()
        return len(candidates)

    def ensure_candidates(self) -> None:
        if self.session.queue:
            return
        self.search(self.last_query or DEFAULT_BOOTSTRAP_QUERY,self.last_artist,max_results=24)

    def next_payload(self) -> dict | None:
        self.ensure_candidates()
        item=self.session.choose_next()
        self.save()
        if item is None:
            return None
        video_id=str(item.metadata.get("video_id",""))
        return {
            "source_id":item.source_id,
            "video_id":video_id,
            "title":item.title,
            "artist":item.artist,
            "duration_s":item.duration_s,
            "embed_url":youtube_embed_url(video_id),
            "state":self.session.run_state.value,
        }


RUNTIME=ResearchRuntime()


class ResearchHandler(SimpleHTTPRequestHandler):
    runtime=RUNTIME

    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(WEB_ROOT),**kwargs)

    def _json(self,payload: object,status: int=200) -> None:
        data=json.dumps(payload,ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(data)))
        self.send_header("Cache-Control","no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed=urlparse(self.path)
        if parsed.path in {"/research","/research/"}:
            self.path="/research.html"
            return super().do_GET()
        if parsed.path=="/api/research/status":
            self._json({
                "configured":self.runtime.configured(),
                "state":self.runtime.session.run_state.value,
                "current_source_id":(
                    self.runtime.session.current.source_id
                    if self.runtime.session.current else None
                ),
                "completed":len(self.runtime.session.completed_source_ids),
                "failed":len(self.runtime.session.failed_source_ids),
                "blocked":len(self.runtime.session.blocked_source_ids),
                "queued":len(self.runtime.session.queue),
                "last_query":self.runtime.last_query,
                "last_artist":self.runtime.last_artist,
                "canonical_audio_evidence_attached":self.runtime.ingestor.canonical_audio_attached,
                "audio_engine_owner":"music_intelligence.audio_evidence",
                "coordinate_owner":"MusicalScoreCoordinate",
            })
            return
        if parsed.path=="/api/research/search":
            q=parse_qs(parsed.query)
            terms=q.get("terms",[self.runtime.last_query or DEFAULT_BOOTSTRAP_QUERY])[0].strip()
            artist=q.get("artist",[self.runtime.last_artist])[0].strip()
            try:
                count=self.runtime.search(terms,artist,max_results=24)
            except (ValueError,YouTubeDataAPIError) as exc:
                self._json({"ok":False,"error":str(exc)},503)
                return
            self._json({"ok":True,"count":count,"terms":terms,"artist":artist})
            return
        if parsed.path=="/api/research/next":
            try:
                payload=self.runtime.next_payload()
            except (ValueError,YouTubeDataAPIError) as exc:
                self._json({"ok":False,"error":str(exc)},503)
                return
            self._json({"ok":True,"source":payload})
            return
        return super().do_GET()

    def do_POST(self):
        parsed=urlparse(self.path)
        length=int(self.headers.get("Content-Length","0") or 0)
        if length>4*1024*1024:
            self._json({"ok":False,"error":"request too large"},413)
            return
        body=self.rfile.read(length)

        if parsed.path=="/api/research/event":
            try:
                payload=json.loads(body.decode("utf-8") or "{}")
                event=str(payload.get("event",""))
                actions={
                    "playing":self.runtime.session.mark_playing,
                    "analyzing":self.runtime.session.mark_analyzing,
                    "ended":self.runtime.session.mark_complete,
                    "blocked":self.runtime.session.block_current,
                    "failed":self.runtime.session.fail_current,
                    "paused":self.runtime.session.pause,
                    "resume":self.runtime.session.resume,
                }
                if event not in actions:
                    raise ValueError("unsupported research event")
                actions[event]()
                self.runtime.save()
                self._json({"ok":True,"state":self.runtime.session.run_state.value})
            except (ValueError,RuntimeError,json.JSONDecodeError) as exc:
                self._json({"ok":False,"error":str(exc)},400)
            return

        if parsed.path=="/api/research/audio":
            source_id=self.headers.get("X-RealSolo-Source-Id","").strip()
            try:
                sample_rate=int(self.headers.get("X-RealSolo-Sample-Rate","48000"))
                media_time_header=self.headers.get("X-RealSolo-Media-Time","").strip()
                media_time=float(media_time_header) if media_time_header else None
                row=self.runtime.ingestor.ingest_float32(
                    source_id,body,sample_rate=sample_rate,timestamp=media_time
                )
                if self.runtime.session.current is not None:
                    self.runtime.session.mark_analyzing()
                self.runtime.save()
                self._json({"ok":True,**row})
            except (ValueError,RuntimeError) as exc:
                status=409 if "bridge is not attached" in str(exc) else 400
                self._json({"ok":False,"error":str(exc)},status)
            return

        self.send_error(404)


def run_research_web(host: str="127.0.0.1",port: int=8771) -> None:
    server=ThreadingHTTPServer((host,port),ResearchHandler)
    print(f"RealSolo Autonomous Research Listener: http://{host}:{port}/research")
    print("Browser capture requires explicit user permission.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
