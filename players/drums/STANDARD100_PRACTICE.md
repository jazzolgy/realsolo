# Standard100 Bebop Drummer Practice

Private repertoire root:

`REALSOLO_CORPUS_ROOT/symbolic/irealb_v1_0/standard100/`

## Goal

Use the real 100-standard symbolic corpus as **repertoire practice**, not as a
lick memorization database.

The drummer practices:

- ride continuity
- skip-note omission/return
- hi-hat anchor
- phrase-aware snare comping
- retrospective 2–4 hit motif memory
- intentional non-response
- BUILD / COAST / COME_DOWN
- form/section punctuation when source metadata provides boundaries
- walking-bass complementarity
- handoff at source form boundaries

## Source integrity

The loader does not invent missing chart facts.

If meter, tempo, section, or bar count is absent, it stays unknown.
A chart without a parseable source bar count is not run through the form
practice loop.

The runner may apply clearly labeled **exercise overlays** (for example a
default practice tempo or an 8-bar phrase-position drill) when source metadata
is absent.  These overlays are stored separately in the result and never
represented as facts from the chart.

## Copyright / corpus boundary

Raw iReal-derived chart material stays in the private corpus.  The public repo
contains only code, schemas, tests, and research logic.

Derived reports default to:

`REALSOLO_CORPUS_ROOT/derived/drums/standard100/practice_report.json`

The report stores performance statistics, not copied chord charts.

## Deterministic four-pass exercise

Each chart is currently exercised across four interaction passes:

1. rising soloist with drummer headroom — tests BUILD
2. rising soloist after active drummer history — tests COAST
3. post-climax decline — tests COME_DOWN
4. dense soloist/opening alternation — tests intentional non-response

A walking bass projection is active during practice so bass/drums
complementarity is exercised at the same time.

## Important limitation

This ChatGPT execution container does not currently have
`REALSOLO_CORPUS_ROOT` mounted, so the real private 100-song run cannot be
executed from this container.  The runner is designed to run directly in the
RealSolo environment where that environment variable points to the private
corpus.

Command:

`python -m music_intelligence.drums.practice_standard100 --passes 4`

Once the real corpus is mounted, the report will show the exact number of files
discovered/parsed/practiced and the resulting behavior metrics.
