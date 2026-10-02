# Parker Intelligence v2 Architecture

This document fixes the Charlie Parker architecture for RealSolo.

## Separation of concerns

SOURCE -> OBSERVATION -> VOCABULARY / ABSTRACTION -> RUNTIME PRIOR

Parker is a LegendProfile, not the definition of Bebop. General Bebop grammar
must be supported across musicians before promotion to music_intelligence/style/bebop.

## Jazz vocabulary rule

RealSolo does not prohibit stored licks or literal quotations. Licks, motifs,
fragments, cliches and phrase vocabulary are legitimate components of jazz
memory. The system preserves source and musical context and may quote,
transpose, adapt, fragment, abstract, or hybridize them according to current
harmony, form, phrase, ensemble state, and musical intention.

## Online improvisation invariant

Vocabulary can shape intention and candidate families, including
HYBRID_COMPOSITION, but the runtime still commits one current event, listens,
then generates/evaluates candidates again.

## Instrument boundary

Parker-specific physical tendencies are legend evidence.
Generic Sax feasibility belongs to players/sax/.

## Common interfaces

Sax and future players should consume Parker through LegendProfileView and
VocabularyQuery rather than importing Parker-specific files into the player
package.
