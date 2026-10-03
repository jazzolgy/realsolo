# Public Analysis Artifact Policy

## Principle

RealSolo preserves derived music-analysis results in the public repository by
default when doing so is useful for reproducibility, engine validation, research
history, or future learning-system development.

**DERIVED_ONLY is a training-rights disposition. It does not mean PRIVATE.**

A source may therefore be:

- copyrighted / owner-supplied;
- not admitted for model training;
- still the basis for public derived analysis artifacts.

Publication and training admission are separate decisions.

## Default publication classes

### PUBLIC_DERIVED

Preferred default for analysis results that do not embed source audio or a
substantial facsimile of a copyrighted score.

Examples:

- event timestamps and event IDs;
- beat/bar/chorus hypotheses;
- pitch hypotheses with uncertainty;
- instrument and role probabilities;
- separate pitch/onset/duration/instrument/alignment confidence;
- spectral/timbre descriptors;
- dynamics, articulation and microtiming evidence;
- harmony-relative and score-position evidence;
- phrase / motif / gesture grouping;
- ensemble-interaction events;
- density, register, silence, response-delay and role statistics;
- attribution revisions and hard-example metadata;
- analysis parameters, failure cases, tests and evaluation summaries.

Detailed event-level analysis is not reduced to aggregate percentiles merely
because the source recording is copyrighted.

### REVIEW_REQUIRED

Use when a derived artifact approaches a practical substitute for a protected
musical expression or embeds unusually complete source-dependent content.

Examples:

- a complete, clean MIDI-equivalent transcription of a protected composition or
  arrangement;
- an exact full-score reconstruction;
- long verbatim textual/lyric payloads;
- representations deliberately designed for high-fidelity source reconstruction.

Review may result in publication as-is, publication after transformation
(relative intervals, harmonic functions, coarser timing, omitted melody payload),
or keeping only that specific payload local.

### LOCAL_SOURCE_ONLY

Do not commit:

- raw copyrighted audio;
- separated full-length source stems from that audio;
- scans or facsimiles of copyrighted score pages except where independently
  permitted;
- secrets, credentials, or private source files.

## Research preservation rule

When a public artifact can preserve an analysis result without embedding the
source itself, preserve the analysis.

Do not throw away useful results solely because the source was copyrighted.
Prefer provenance, uncertainty, and source identifiers over deletion.

## Rights and learning remain distinct

The Shared Learning Engine continues to respect the corpus rights gate:

- TRAINING_ELIGIBLE may update trainable/adaptive priors;
- DERIVED_ONLY may be studied as evidence but does not update trainable priors
  without explicit permission.

Public visibility does not grant training permission.

## Autumn Leaves / BE-003

BE-003 remains DERIVED_ONLY for learning admission. Its analysis artifacts are
PUBLIC_DERIVED by default.

The public repository should therefore retain score/form hypotheses,
event-level uncertainty, instrument attribution, revision history, interaction
analysis, validation failures, and engine-improvement checkpoints.

Raw playlist audio and source-derived full stems remain outside the repository.
