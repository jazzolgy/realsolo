# Notation Engine Boundary

## Purpose

The notation engine is part of the Music Intelligence Platform today, but it must remain capable of becoming an independent commercial product later.

The target is **architectural separability before repository separability**.

Do not fork or duplicate the engine prematurely. First stabilize the contracts that let both RealSolo and a future standalone notation application use the same implementation.

## Product roles

### Inside RealSolo

The notation engine may render:

- live chord charts;
- player parts;
- optional full score;
- readable records of AI Player or human committed performances;
- MusicXML/export artifacts.

### Future standalone notation application

The same engine should support:

- audio upload;
- MIDI import;
- recorded/live performance intake;
- automatic transcription;
- score cleanup and engraving;
- readable part/full-score generation;
- editing and export.

The standalone product must not require the RealSolo realtime or ensemble runtime.

## Dependency rule

Allowed direction:

```text
Shared Music Semantics / UMR contracts
              ↓
      Performance Evidence
              ↓
       Notation Engine
              ↓
 Logical Score / Engraving
              ↓
 Renderer / MusicXML / Product UI
```

Forbidden direction:

```text
Notation Engine
→ RealSolo realtime scheduler
→ Player generation policy
→ ensemble interaction state machine
→ RealSolo-specific UI
```

RealSolo-specific behavior belongs in an adapter.

## Stable boundary objects

The engine should converge on versioned, serializable contracts for:

1. **Performance Evidence**
   - physical/performed onset and offset
   - pitched or unpitched evidence
   - articulation / ornament / technique
   - player / instrument / role identity
   - phrase / form / harmony references when known
   - factorized confidence
   - alternatives, evidence and provenance

2. **Notation Intent / Candidates**
   - include / omit / optional decisions
   - readable rhythm interpretation
   - spelling alternatives
   - voice/staff allocation alternatives
   - fidelity, readability and complexity costs

3. **Logical Score**
   - notation-domain score model independent of a renderer
   - parts, staves, voices, measures, events, directions and spanners

4. **Renderer / Export adapters**
   - MusicXML
   - future native renderer(s)
   - future PDF/SVG/rendering backends
   - future standalone editor UI

## Core separation principles

- Performance Representation != Notation Representation.
- Microtiming is evidence, not automatically literal notation.
- Notation may simplify a performance for readability without mutating the original Performance Evidence.
- MusicXML is an output/interchange format, never the UMR.
- Instrument notation profiles belong to notation semantics; instrument improvisation policy belongs to Players.
- Exact page geometry and house-style controls are secondary to readable, playable automatic notation.

## Integration strategy for the current repository

The existing `transcribe` branch has developed substantially and is currently divergent from `main`. Do **not** merge the branch wholesale.

Integrate in slices:

1. freeze and document shared boundary contracts;
2. port notation-domain data models with no RealSolo runtime dependency;
3. port rhythm/spelling/allocation/score logic;
4. port engraving/layout and MusicXML adapters;
5. port RealSolo adapter separately;
6. run shared regression tests against current `main`;
7. only after the API stabilizes, decide whether to extract a standalone package/repository.

## Extraction criterion

A separate repository/package becomes appropriate when all of these are true:

- source adapters are replaceable;
- notation engine imports no RealSolo application code;
- Performance Evidence and Logical Score are serialized/versioned;
- engine tests run without the RealSolo runtime;
- RealSolo consumes the engine only through public APIs;
- standalone release cadence or commercial requirements justify independent packaging.

Until then, keep one repository and enforce the boundary in code and tests.
