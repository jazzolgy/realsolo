# RealSolo Study MVP

This is the first runnable study tool on current Shared Core.

It is intentionally small enough to run now while preserving the canonical
architecture:

- persisted musical position is only `MusicalScoreCoordinate`;
- source seconds remain provenance/navigation;
- local audio is decoded transiently and is not persisted by the tool;
- compact non-reconstructive evidence becomes Shared Learning artifacts;
- unaligned windows are stored as navigation evidence but do not update research
  priors;
- an explicit manual form clock is a temporary alignment bootstrap, not a second
  form theory.

## Install

Python 3.11+ and ffmpeg are required.

    pip install -e ".[study]"

## Fastest first run

Study the first two minutes of any local MP3 without claiming musical position:

    realsolo-study album.mp3 \
      --source-id local:first_pass \
      --max-seconds 120 \
      --output study_first_pass.jsonl

This produces compact window evidence. Because no musical alignment was supplied,
each row is marked `navigation_only`.

## Start form-aware study immediately

Until automatic Beat/Downbeat/Form Intelligence is production-ready, supply an
explicit alignment clock. The clock is converted directly into canonical
`MusicalScoreCoordinate` objects.

Example for a 32-bar 4/4 form:

    realsolo-study autumn_leaves.mp3 \
      --source-id bill_evans:autumn_leaves:take1 \
      --song "Autumn Leaves" \
      --bpm 206.7 \
      --meter 4/4 \
      --form-bars 32 \
      --form-start-s 8.0 \
      --sections "A1:1-8,A2:9-16,B:17-24,C:25-32" \
      --phase head \
      --output autumn_leaves_study.jsonl

The persisted rows then contain positions such as:

    Autumn Leaves / A1 / chorus 0 / bar 1 / beat 1
    Autumn Leaves / B  / chorus 0 / bar 18 / beat ...
    Autumn Leaves / C  / chorus 1 / bar 31 / beat ...

Those positions, rather than elapsed seconds, are the learning address.

## Studying one track inside a long compilation

Use `--start-s` to seek into a compilation while preserving source-relative
seconds in the evidence.

Existing repository research identifies the Bill Evans *Autumn Leaves* segment
in one project compilation at approximately 11:48–17:49, with the head beginning
about eight seconds into that track. A bootstrap run can therefore look like:

    realsolo-study bill_evans_compilation.mp3 \
      --source-id bill_evans:portrait_in_jazz:autumn_leaves_take1 \
      --start-s 708 \
      --max-seconds 361 \
      --song "Autumn Leaves" \
      --bpm 206.7 \
      --meter 4/4 \
      --form-bars 32 \
      --form-start-s 716 \
      --sections "A1:1-8,A2:9-16,B:17-24,C:25-32" \
      --output autumn_leaves_take1_study.jsonl

The exact alignment remains research evidence, not immutable truth. The current
repository alignment file should be used to refine it.

## Output

Each JSONL row contains:

- source identity;
- source-time window;
- RMS / peak;
- zero-crossing rate;
- spectral-centroid proxy;
- local onset-rate proxy;
- bounded activity proxy;
- canonical `MusicalScoreCoordinate`, when available;
- artifact ids;
- learning status.

The tool emits two Shared Learning artifacts per window:

- `study.audio_window.rhythm.v1`
- `study.audio_window.expression.v1`

They are ingested with:

    learn=False
    study_as_evidence=True

so research material does not silently become training-authorized material.

## What this MVP does not claim

It is not yet:

- a polyphonic transcription system;
- a production beat/downbeat detector;
- an automatic form recognizer;
- a RealChord raw-chart structural parser;
- a player-specific source-separation system;
- a final jazz-instrument classifier.

Those components should be attached to the same study session later. The point
of this MVP is to make the evidence pipeline runnable now without violating the
canonical Shared Core boundaries.

## Next step

The next upgrade should replace/manual-assist the `ManualFormClock` with Shared
Beat/Downbeat/Meter/Form Intelligence, then attach RealChord Expected Harmony to
the resulting `MusicalScoreCoordinate`.


## Reuse an existing verified research alignment

The preferred bootstrap is to reuse an existing research alignment manifest
rather than type a new manual clock.

For the existing Bill Evans *Autumn Leaves* research:

    realsolo-study bill_evans_compilation.mp3 \
      --source-id bill_evans:portrait_in_jazz:autumn_leaves_take1 \
      --start-s 708 \
      --max-seconds 361 \
      --song "Autumn Leaves" \
      --alignment-json research/legends/bill_evans/observations/score_alignment/autumn_leaves_take1_sections_v0_1.json \
      --alignment-offset-s 708 \
      --output autumn_leaves_take1_study.jsonl

The alignment manifest is evidence, not a new canonical coordinate. Its verified
time/bar windows are converted into `MusicalScoreCoordinate` at ingestion.
Windows outside the manifest's supported ranges remain navigation-only.

This allows the project to begin studying the actual recording immediately while
automatic Beat/Downbeat/Meter/Form Intelligence is still being developed.
