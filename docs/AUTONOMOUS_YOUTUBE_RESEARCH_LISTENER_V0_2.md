# Autonomous YouTube Research Listener v0.2

RealSolo may run a long-lived, gap-driven YouTube research session when a user
has explicitly started research playback in the visible research UI.

The feature is designed as a research workflow, not a media downloader.

## Default autonomous loop

```text
current research coverage
        ↓
ResearchGap[]
        ↓
priority override (optional)
        ↓
highest underrepresented musician/style/instrument/dimension
        ↓
YouTube search provider
        ↓
ResearchSourceCandidate[]
        ↓
eligibility / duplicate / recent-use ranking
        ↓
visible embedded playback
        ↓
user-authorized tab/system audio capture
        ↓
Audio Evidence Engine
        ↓
Performance Evidence
        ↓
MusicalMoment / structural study
        ↓
evidence-only Learning / Legend research store
        ↓
coverage update
        ↓
next gap
```

There is no fixed default curriculum. User instructions such as "study piano
for now", "move from Parker toward Coltrane", or "prioritize harmony over
interaction" are represented as temporary `ResearchPriorityOverride` weights.

## Ownership

- Research Priority owns what is underrepresented and what should be searched.
- YouTube provider adapter owns provider search metadata and embeddable identity.
- Browser research player owns normal visible playback.
- Browser/OS capture owns the user-authorized audio stream.
- Audio Evidence Engine owns acoustic observation/posterior evidence.
- Music Intelligence Core owns musical meaning.
- Learning/Legend layers own evidence admission and later promotion.

No layer may treat a YouTube search result itself as musical evidence.

## Resumable session states

The autonomous controller is designed to continue after ordinary long-running
failures:

```text
IDLE
→ SEARCHING
→ READY
→ PLAYING
→ ANALYZING
→ SEARCHING

PAUSED / BLOCKED / FAILED
→ resume
→ READY or SEARCHING
```

Completed, failed, and blocked source IDs are tracked independently so a failed
video is not immediately selected again.

## YouTube boundary

`youtube_research_provider.py` contains a provider contract and maps a normal
search result into `ResearchSourceCandidate`.

The contract exposes only metadata required for research selection:

- video id
- title/channel
- duration
- embeddable/playable flags
- source/identity/audio suitability evidence
- provider metadata

It deliberately does not expose a media-byte API.

Normal playback uses a visible YouTube embed. Audio analysis must enter through
a separately user-authorized browser/OS capture path.

## Next implementation slice

v0.3 should add:

1. actual YouTube Data API search adapter and credentials/config boundary;
2. visible research-player UI using the YouTube IFrame API;
3. ended/error/blocked callbacks into `AutonomousResearchSession`;
4. tab/system-audio capture handshake;
5. Audio Evidence streaming endpoint;
6. durable manifest/checkpoint so a browser restart can resume;
7. coverage updater that creates the next `ResearchGap`.

The first live version should remain supervised enough to inspect source
identity and capture quality before unattended overnight operation is enabled.


## Actual learned instrument model: YAMNet

The first concrete pretrained model attached to the learned-instrument interface is
Google YAMNet (https://tfhub.dev/google/yamnet/1).

RealSolo uses YAMNet as a broad **instrument-presence front end**, not as the final
jazz instrument/role reasoner.

Runtime behavior:

    browser PCM
    -> rolling 0.96-1.92 s analysis window
    -> resample to mono 16 kHz
    -> YAMNet AudioSet class scores
    -> map supported AudioSet instrument/vocal classes
    -> LearnedInstrumentBackend
    -> DetectorEvidence
    -> temporal + beat/phrase/register context correction

Mapped first-class RealSolo targets include piano, guitar, acoustic/double bass,
electric/bass guitar, drums, saxophone, trumpet, flute, and vocal/singing.

YAMNet does not supply jazz ensemble roles. Role probabilities remain a separate
RealSolo inference layer. Generic AudioSet labels are not forced into an
instrument identity.

The model is selected by default for the Autonomous Research Listener. Install
the optional dependencies with:

    pip install -e ".[research-ml]"

To explicitly disable the learned model and use the conservative acoustic
baseline:

    export REALSOLO_INSTRUMENT_MODEL=baseline

A separately configured REALSOLO_INSTRUMENT_MODEL_URL still overrides the
built-in YAMNet backend for local custom/production model services.

The model loads lazily on first usable analysis window. If the package/model is
unavailable, the hybrid detector falls back to the conservative baseline rather
than stopping the long-running research session.
