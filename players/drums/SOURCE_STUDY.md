# AI Drummer Source Study Map

This document tracks how the uploaded drum library is being converted into
RealSolo drummer knowledge.  It deliberately separates **literal source
patterns**, **derived performance grammar**, and **decision principles**.

## Core sources under deep ingestion

### John Riley — The Art of Bop Drumming

The book is organized around Time Playing, Comping, Soloing, Brushes, and More
Jazz Essentials.  The latter explicitly covers Shuffle, playing in 2, 3/4,
Samba, 12/8, Mambo, and Uptempo Playing.

Corpus use:
- literal ride/time patterns
- pedal hi-hat 2/4
- comping/independence families
- brush time and ballad grammar
- shuffle, 2-feel, 3/4, samba, 12/8, mambo, uptempo style families

### John Riley — Beyond Bop Drumming

Core topics include broken/modern time, three-voice comping, uptempo studies,
implied time/metric modulation, and solo ideas.  Its historical discussion is
especially important: modern time-playing can derive forward motion from the
combined drum-set voices rather than a fixed ride ostinato, and the hi-hat may
operate contrapuntally.

Corpus use:
- irregular/modern ride vocabulary
- three-voice comping patterns
- broken-time transformations
- implied-time and metric-modulation constraints
- advanced solo phrase families

### Bob Moses — Drum Wisdom

Primary conceptual source for attitude, internal hearing, groove canon, 8/8,
combining points, movable two, non-independent method, yin/yang triplets,
organic drumming, movement/dancing, and singing.

The key AI consequence is that a drummer should play **off something**:
melody, bass line, vamp, ensemble event, remembered material, or an internally
heard idea.  Internal hearing provides continuity so external listening does
not destroy the underlying structure.

Corpus use:
- decision/reward rules
- referent-aware comping
- internal-time model
- groove/phrase transformation principles

### Kim Plainfield — Advanced Concepts

This is the broadest style-expansion source in the upload set.  The table of
contents includes funk, shuffle, linear funk, swing-time conversion, swing
triplets, Brazilian rhythms (samba, baiao), Afro-Cuban rhythms (Mozambique,
guaguanco, mambo, songo), 6/8, and advanced rhythmic concepts.

The Afro-Cuban pages explicitly connect clave orientation to cascara and other
grooves, so these patterns must carry structural clave metadata rather than be
treated as freely interchangeable two-bar loops.

Corpus use:
- funk/linear-funk pattern families
- swing-triplet independence
- samba and Brazilian coordination
- son/rumba clave-aware Afro-Cuban grammar
- cascara, Mozambique, guaguanco, mambo, songo, 6/8
- voice/limb orchestration transformations

### Marc Atkinson / Vinnie Colaiuta — The UnReel Drum Book

Queued as a high-value advanced transcription source.  Contents include rhythm
scale exercises, foot ostinatos, shifting scales, rhythmic displacement,
transcriptions/solo breakdowns, and five-against-four / seven-against-four
polyrhythms.

Planned use:
- advanced subdivision and polymeter/polyrhythm vocabulary
- Vinnie-specific LegendProfile evidence
- high-complexity physical-feasibility benchmarks

## Supporting sources

### Ron Spagnardi — Big Band Drumming: Understanding Fills
Literal setup/fill patterns and ensemble-figure targeting.  Already seeded in
the source pattern corpus.

### Jim Holland — The Complete Book of Drum Fills
Organizes fills by rhythmic material and duration: one-beat, half-measure,
one-measure, two-measure; eighth, sixteenth, triplet, and combinations.  It
also explicitly treats sticking choice, optional crash resolution, steady time,
accents, and space as musical material.

### Ray F. Badness — Drum Programming
Useful for a realizability baseline: kick/snare, hi-hat/ride, toms, fills,
cymbals, arrangement sections, and the practical requirement to think in terms
of a human drummer rather than unconstrained sequencer lanes.

### Berklee — Drum Set Notation in Finale
Schema/reference source for PAS notation, hand/foot stem direction, kit
positions, percussion maps, and MIDI-to-notehead/staff mapping.

## Vocabulary/reference sources

The remaining uploaded books are retained in the source catalog rather than
discarded: Drum Fundamentals, Alfred's Drum Method, Kevin Tuck tutorials,
Snare Drum, Drum Soloist, Modern Drummer article scans, 100 Legendary Rock Drum
Fills, Encyclopedia of Drum Terms, and the uploaded mixed drum-pattern book.

These are lower priority for *decision intelligence* but remain useful for:
- rudiments and sticking
- reading/subdivision vocabulary
- rock/fill vocabulary
- physical feasibility
- terminology and notation
- later exact-pattern transcription

## Ingestion rule

Every source-derived item must be one of:

1. **Exact source pattern** — symbolic hits/orchestration transcribed from a
   specific page/example.
2. **Pattern family** — a source-supported family without pretending that one
   specific transcription is universal.
3. **Decision rule** — source-supported reason/constraint about when or why to
   play.
4. **Technique/feasibility rule** — limb, sticking, articulation, notation, or
   physical constraint.

The runtime may retrieve complete patterns as knowledge, but commits only the
current gesture before listening again.
