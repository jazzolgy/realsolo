# Autonomous Research Listener — Current Integrated Status (2026-10-04)

This document consolidates the current state of the Autonomous Research Listener
and its integration with Shared Music Intelligence.

## 1. Ownership boundary

The Autonomous Research Listener does **not** own musical understanding.

It is responsible for:
- autonomous source selection / playback orchestration,
- visible YouTube embed control,
- user-authorized browser/system audio capture,
- forwarding PCM/evidence into Shared Music Intelligence,
- storing research evidence/provenance,
- checkpoint/resume behavior.

Shared Music Intelligence owns:
- instrument / role interpretation,
- beat / meter / phrase interpretation,
- form interpretation,
- harmony interpretation,
- canonical musical position,
- ensemble context,
- learning admission.

This keeps drums, piano, bass, sax, research tools and future players on the same
musical world model.

## 2. YouTube research loop

The current research listener architecture supports:

    search metadata
      -> visible official embed
      -> user-authorized display/tab audio capture
      -> Float32 PCM
      -> Shared Audio Intelligence
      -> research evidence / musical moments
      -> checkpoint / next-source loop

YouTube metadata is source-selection metadata only. It is never treated as
musical evidence.

The design does not depend on hidden playback, source-media downloading, DRM
bypass, or media extraction.

## 3. Instrument intelligence

The first attached pretrained model is Google YAMNet.

Pipeline:

    browser PCM
      -> rolling analysis window
      -> mono 16 kHz resample
      -> YAMNet AudioSet scores + embedding
      -> RealSolo instrument mapping
      -> DetectorEvidence
      -> temporal / beat / phrase / register correction

Current first-class targets include:
- piano
- acoustic/double bass
- drums
- saxophone
- trumpet
- guitar
- electric bass
- vocal
- flute

YAMNet is treated as instrument-presence evidence, not as a jazz-role model.

A persistent JazzInstrumentEmbeddingHead can adapt to recurring jazz timbres.
Automatic admission is conservative; ambiguous examples are rejected.

The research UI also provides an explicit supervised-correction path:

    current YAMNet embedding
      -> user-selected baseline instrument label
      -> persistent prototype update

Only embedding prototypes/counts are persisted by this adaptation layer, not
source audio.

## 4. Optional source separation

The runtime contains an optional source-separation boundary.

A localhost separator may produce temporary in-memory stems. A learned
instrument backend can classify those stems and fuse their evidence.

Remote audio endpoints are rejected by default unless explicitly enabled.

The separator/model service boundaries are optional. Their failure should fall
back to the conservative baseline rather than stop a long-running research
session.

## 5. Raw evidence vs contextual interpretation

The shared evidence hierarchy keeps detector evidence separate from musical
context correction:

    DetectorEvidence
      -> ContextCorrection
      -> PerformanceEvidence
      -> MusicalMoment
      -> StructuralPerformanceEvent (only when timing/address requirements hold)

Raw detector output is not overwritten by contextual reasoning.

Unknown values remain unknown (`None`) rather than being coerced to numeric
zero.

## 6. Canonical learning coordinate: musical form, not elapsed time

RealSolo now treats musical position as the canonical learning coordinate.

Source time answers:

    "when did this happen in the recording?"

Canonical form position answers:

    "where did this happen in the music?"

Learning uses the second.

The shared address is represented by `MetricFormPosition` / `FormMap` and can
include:

    form
      -> hierarchical section path
      -> recurrence / chorus iteration
      -> measure
      -> beat in measure
      -> local microtiming

Examples:

    jazz:
      AABA32 -> B -> chorus 2 -> measure 19 -> beat 3

    pop:
      verse_2 -> measure 3 -> beat 2

    classical:
      movement_1 -> exposition -> primary_theme -> measure 5 -> beat 1

Hierarchical sections allow flat pop forms, cyclic jazz forms and nested
classical forms to share one architecture.

## 7. Meter handling

Canonical beat position is expressed in the active meter's denominator units.

Examples:
- 4/4: beat positions 0,1,2,3 map to written beats 1,2,3,4.
- 6/8: positions 0..5 represent eighth-note locations.
- meter changes can be represented with `MeterSegment` entries in a `FormMap`.

This keeps exact notated position separate from higher-level compound-pulse
grouping.

## 8. Form-conditioned learning

Every derived learning artifact can carry musical form context.

The same musical material at different positions remains distinct evidence.

For example:

    A-section bar 7 beat 4

and

    bridge bar 23 beat 4

must not collapse into one positionless observation.

SharedLearningEngine can accumulate form-conditioned priors by:

    form / section / measure / beat

Repeated choruses normalize to the same form-relative location for comparison,
while exact `form_iteration` remains available for longitudinal study.

This supports questions such as:
- how does comping density change at the same form bar across choruses?
- how does setup behavior change near a form boundary?
- how does the same phrase location differ by performance phase?

## 9. Unresolved evidence policy

Audio may arrive before meter/form alignment is known.

In that case:

    source_time = known
    musical position = unresolved

The evidence may be stored for navigation and later re-analysis, but unresolved
metric evidence must not update musical learning priors.

Structural promotion requires a resolved measure + beat address.

This prevents elapsed-time or weak acoustic guesses from becoming false musical
knowledge.

## 10. Shared Form Intelligence

Form interpretation now belongs to Shared Music Intelligence through
`SharedFormIntelligence`.

Consumers include:
- Autonomous Research Listener
- AI Drummer
- future piano / bass / sax / other players
- learning / retrieval systems

Shared Form Intelligence accepts runtime evidence such as:
- absolute musical beat when reliably available,
- meter evidence,
- form prior / form map,
- phrase identity,
- performance phase,
- arrangement segment,
- boundary probability.

It outputs one shared form state with:
- canonical position,
- performance phase,
- arrangement segment,
- within-core-form state,
- distance to a known boundary,
- confidence.

The research listener does not duplicate this logic.

## 11. Corpus / RealChord integration boundary

Shared corpus discovery now recognizes form-relevant sources tagged as:
- realchord
- form_annotation / form_map
- measure_map
- meter_map
- downbeat_map
- chord_chart
- score / lead_sheet

Discovery prioritizes explicit RealChord/form/downbeat evidence over generic
chart sources.

Corpus metadata is prior/expected structure only. It is not treated as proof of
what the performed audio actually did.

A concrete adapter must convert a visible registered corpus item into a FormMap,
score alignment, expected harmony, or other structured evidence.

At the time of this integration pass, no corpus item/file named `RealChord` was
visible in the public repository tree or connected Library search results, so no
file format was invented. The discovery boundary is ready to consume it once it
is registered/visible.

## 12. Current UI / research observability

The research UI exposes:
- capture/listener state,
- RMS / pitch evidence,
- instrument posterior,
- role posterior,
- tempo / beat,
- register,
- learned model state,
- canonical musical position.

Form position is shown as either a resolved address or:

    unresolved · navigation only

## 13. Current implementation limits

Important remaining gaps:
- production-grade beat/downbeat/meter inference is not yet connected to
  `SharedFormIntelligence`.
- automatic form/section inference from performed audio is not yet production
  quality.
- Observed Harmony front-end still needs to be attached.
- RealChord parsing cannot be implemented until the actual registered file/item
  format is visible.
- autonomous curriculum/query generation remains less complete than the runtime
  listening/evidence architecture.
- a production jazz-specific supervised instrument classifier still needs
  curated/labelled data beyond YAMNet self-distillation.

## 14. Next implementation order

1. Connect Beat / Downbeat / Meter Intelligence to Shared Form Intelligence.
2. Consume registered RealChord/form-map corpus sources as expected structure.
3. Add performed-audio form alignment and section-boundary inference.
4. Attach Observed Harmony to the same canonical position.
5. Finalize source-level evidence accumulation into SharedLearningEngine using
   evidence-only admission for research-derived material.
6. Continue autonomous research-gap planning and query generation.

## 15. Architectural invariant

The central invariant is:

    one shared musical intelligence
    + one canonical musical address
    + many instrument/player consumers

No player, research listener, or transcription component should create a private
form theory when shared musical-position knowledge already exists.
