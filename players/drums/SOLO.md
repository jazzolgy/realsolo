# Drum Solo Intelligence

A RealSolo drum solo is not a long fill.  It is an improvisation process with
memory, development, contrast, tension, space, form awareness, and ensemble
re-entry.

## Source-derived design

### The Art of Bop Drumming

The solo chapter explicitly treats solo structure and develops a one-bar phrase
through a sequence of operations:

1. repetition
2. orchestration around the kit
3. adding rests to create space/displacement
4. removing notes inside the phrase
5. rhythmic elasticity (stretching or compressing the perceived rhythm)
6. three-beat phrases that cycle across 4/4
7. introduction of a second idea and further orchestration

This becomes the baseline **motif-development grammar**.

### Beyond Bop Drumming

The later book extends solo language toward longer modern-jazz phrases,
three-beat phrases with rests, triplets grouped in fours, variations, and
examples associated with post-bop drummers.

This becomes the advanced **displacement / metric-illusion grammar**.  These
devices should not appear simply because they are technically available; they
are controlled by arc, adventurousness, accumulated phrase context, and the
need to remain legible to the ensemble/listener.

### The UnReel Drum Book

The transcribed Vinnie Colaiuta material provides high-complexity subdivision
and displacement vocabulary.  In the America solo breakdown, the source
explicitly analyzes a 5-5-5-6 grouping and then practices shifting the material
over sixteenth-note positions.  This is stored as an exact **structural** source
cell rather than pretending every kit hit has already been reliably
machine-transcribed.

## Runtime model

The solo engine maintains local execution state only:

- number of statements/spaces
- motif repetition count
- last orchestration voice
- last development operation

Shared Core remains responsible for form/phrase/narrative/ensemble semantics.

At each call the solo engine considers immediate actions such as:

- state motif
- repeat
- orchestrate
- add space
- internal rest
- displace
- three-beat cycle
- metric illusion
- contrast
- recap
- resolve/re-enter ensemble

Only one immediate gesture is committed.  The next action is chosen after
listening again.

## Solo quality principle

Technical complexity is not the target.  A strong solo should demonstrate:

- recognizable ideas
- transformation rather than random novelty
- controlled repetition
- meaningful space
- orchestration that changes color without destroying identity
- rhythmic tension that remains related to a perceivable pulse
- dynamic/narrative arc
- awareness of song form
- deliberate ensemble re-entry
- optional advanced metric/subdivision language when stylistically justified

This gives evaluation targets beyond raw speed or note density.


## Shared motif / Legend vocabulary path

The current canonical path is:

`Legend VocabularyMemoryItem`
→ `Shared MotifIdentity`
→ drummer rhythmic projection
→ one current drum event
→ listen
→ re-plan

The Drum Player must not parse a legend source into a private competing memory
schema when Shared Motif Intelligence can represent the same identity.

### Promotion gate

A detected rhythmic cell is **not** automatically runtime vocabulary.

Promotion requires enough evidence to distinguish:
- stable drummer language
- tune/session-specific behavior
- generic swing/subdivision structure
- onset-detector or source-separation artifact

Preferred evidence order:
1. manually verified drum transcription or isolated/source-separated drums
2. recurrence in an independent recording by the same drummer
3. robustness across detector/grid settings
4. context/form annotation

A cell that fails robustness remains in `research/legends/.../observations` or
a provisional vocabulary set and must not enter the active Legend runtime index.

The Eliot Zigmund `Without a Song` 2-3-1 / 1-3-2 / 3-1-2 cells are the first
explicit example: they were initially promoted, then demoted after a broader
robustness check showed detector sensitivity and low recurrence.
