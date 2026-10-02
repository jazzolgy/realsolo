# Bill Evans Trio Multi-Pass Listening Study v0.1

## Scope

Source: project-owner supplied Bill Evans compilation, segmented from the
owner-supplied timestamp list (BE-001..BE-024).

This study is deliberately **observation first**. It does not promote runtime
rules yet.

Primary comparison set with project scorebook matches:

- BE-001 Waltz For Debby — NewReal1 p.387
- BE-002 My Foolish Heart — Realbk1 p.307
- BE-003 Autumn Leaves — NewReal1 p.12 / Realbk1 p.36
- BE-004 Blue In Green — Realbk1 p.53
- BE-006 Someday My Prince Will Come — NewReal1 p.326 / Realbk1 p.388
- BE-010 Nardis — Realbk1 p.316
- BE-011 Alice In Wonderland — Realbk1 p.12
- BE-015 Israel — Realbk1 p.240
- BE-016 Peri's Scope — NewReal2 p.288 / Realbk1 p.347

Do not attribute a behavior to a specific bassist until recording/personnel
identity is separately verified.

## Listening passes

### Pass 1 — whole-trio role map

Listen for:
- who owns foreground at each form position;
- who carries time when another player loosens it;
- density transfer rather than simple accompaniment;
- response delay after another player finishes a phrase;
- form-boundary behavior;
- head vs solo vs out-head changes.

### Pass 2 — bass-only attention

For every section, annotate:
- time-carrier vs harmonic-clarifier vs counterline vs foreground;
- root/non-root structural placement;
- stepwise vs skip vs chromatic connection;
- repeated-note use;
- register center and excursions;
- direction changes;
- note-body length;
- attack hardness;
- accent position;
- ghost/dead/muted-like events where audible;
- quarter-note floor vs inserted subdivisions;
- phrase-end simplification or release;
- response to piano density;
- response to drum activity.

### Pass 3 — score-position comparison

For every available score:
- align form section;
- note what the page explicitly says;
- mark what the trio preserves;
- mark what is reinterpreted;
- distinguish chord-position behavior from phrase-position behavior;
- distinguish recurring behavior from one-off events.

## First comparative observations

These are working observations, not promoted Legend priors.

### BE-001 Waltz For Debby

Score context: medium jazz waltz with clear sectional form.

Working observation:
- The bass role should not be modeled as one invariant "3/4 walking" policy.
- Waltz pulse can remain clear while the bass changes between grounding,
  directional connection and conversational counter-motion.
- The useful research target is **role by phrase/form position**, not a fixed
  beat-1/root + beat-3/approach formula.
- Listen specifically for when the bass line becomes more melodic while the
  piano leaves harmonic/rhythmic space.

### BE-002 My Foolish Heart

Low-level scan: onset rate is much lower than the medium/up swing titles and
dynamic variation is relatively large.

Working observation:
- Bass function is often closer to **harmonic gravity + breath** than continuous
  information delivery.
- Long note body, delayed/restrained attack and release placement matter as
  much as pitch choice.
- A ballad bass policy should be allowed to omit expected connective notes.
- "Correct harmony on every beat" would overplay this context.

### BE-003 Autumn Leaves

Score context: medium swing, repeated ii-V / tonic motion with a clearly
recognizable sectional layout.

Working observation:
- This is a strong test for separating **harmonic roadmap knowledge** from
  formulaic walking.
- Continuous time can coexist with substantial contour variation.
- Bass intelligence should know the recurring harmonic cycle but must avoid
  restating the same role grid on each recurrence.
- Candidate evaluation should compare the same harmonic position across
  multiple choruses to see how register, approach type, articulation and
  direction change while function remains stable.

### BE-004 Blue In Green

Score context: compact slow-form harmonic cycle with strong color/voice-leading
importance.

Low-level scan: lower onset density and high dynamic fluctuation.

Working observation:
- Bass is not primarily a quarter-note clock here.
- Note duration, decay and silence are structural.
- A small number of attacks can carry strong harmonic meaning.
- Voice-leading target quality should outweigh generic walking density.
- The important unit is often a **harmonic arrival plus its decay**, not the
  next beat.

### BE-006 Someday My Prince Will Come

Score context: jazz waltz.

Working observation:
- Compare directly against Waltz For Debby to avoid treating all 3/4 contexts
  alike.
- Measure whether bass accent hierarchy and density depend on melody/section
  position rather than meter alone.
- Track whether inserted subdivisions increase near phrase transitions and
  decrease when the piano foreground becomes dense.

### BE-010 Nardis

Score context: modal/minor-centered repeated form.

Low-level scan: unusually strong low-frequency energy in this compilation.

Working observation:
- This is a key test for **modal grounding vs chord spelling**.
- Bass may create identity through register, repeated/pedal-like gravity,
  contour and rhythmic insistence rather than enumerating every chord member.
- Repetition can be intentional structural identity, not a failure of
  variation.
- The model needs to distinguish "productive repetition" from template
  repetition.

### BE-011 Alice In Wonderland

Score context: jazz waltz.

Low-level scan: one of the highest onset rates in the priority set.

Working observation:
- Useful contrast with the two other waltz studies.
- High event activity does not necessarily imply loss of pulse floor.
- Study the bass as an independent melodic participant while checking that
  form and meter remain legible.
- This track is especially valuable for testing trio equality: bass activity
  may rise without becoming foreground in the same way as a conventional solo.

### BE-015 Israel

Score context: compact standard form with clear harmonic landmarks.

Low-level scan: strong low-frequency energy.

Working observation:
- Study how the bass marks structural arrivals without over-accenting every
  chord change.
- Separate "low-frequency presence" from "high note density".
- Accent placement and note length may be better role indicators than raw
  number of notes.

### BE-016 Peri's Scope

Score context: medium-up swing with written section/solo roadmap.

Working observation:
- Good test for faster harmonic throughput.
- Compare whether the bass simplifies pitch vocabulary when harmonic rhythm is
  fast, while maintaining directional contour.
- Study how repeated chorus positions are varied through register, articulation
  and route choice instead of harmony re-analysis.

## Cross-track bass hypotheses to test

### H1 — Time floor is role-dependent, not a fixed rhythm template

"Keeping time" may mean:
- continuous quarter-note walking;
- sparse but metrically decisive attacks;
- waltz grounding;
- repeated/pedal identity;
- long harmonic anchors.

Therefore RealSolo Bass should model **time-floor semantics** separately from
surface note density.

### H2 — Note body is a musical decision

For bass, sounding length, attack and decay are not renderer polish.

They participate in:
- phrase release;
- harmonic weight;
- foreground/background role;
- perceived swing;
- room for piano/drums.

PerformanceExpression should eventually condition note body on score/form
position and current ensemble role, not only local candidate type.

### H3 — Accent is relational

A bass accent is meaningful relative to:
- previous bass attacks;
- piano density/attack;
- drum setup or fill;
- phrase/form boundary.

Do not learn a fixed "strong beats" accent table from this corpus.

### H4 — Productive repetition and mechanical repetition are different

Nardis-like grounding may require intentional repeated identity.

Anti-template pressure must therefore distinguish:
- repeated role because the music needs a stable identity;
- repeated role because the candidate scorer lacks alternatives.

### H5 — Bass/piano complementarity may be more important than raw bass variety

When piano texture thickens, bass may:
- simplify;
- sustain;
- reduce upper chord information;
- stabilize register.

When piano opens space, bass may:
- connect;
- answer;
- extend contour;
- briefly increase subdivision.

This should be tested position-by-position rather than assumed globally.

## Quantitative navigation aid

The existing low-level feature scan is useful only to choose listening regions.

Among the initial comparison set:
- My Foolish Heart and Blue In Green have relatively low onset density.
- Waltz For Debby, Autumn Leaves and Alice In Wonderland have relatively high
  onset density.
- Nardis and Israel show especially strong low-frequency energy in the mixed
  recording.

These measurements do **not** isolate bass from piano/kick and must never be
promoted directly into a bass LegendProfile.

## Next annotation pass

For each priority track create timestamped windows:

1. head opening;
2. first clear phrase transition;
3. middle-chorus piano foreground;
4. bass-activity increase / foreground handoff where present;
5. final chorus/out-head;
6. ending.

Each window should record:
- score section / harmonic location;
- piano RH/LH role;
- bass role;
- drums role;
- bass attack/body/accent;
- bass route family;
- ensemble-density relation;
- confidence;
- whether the observation recurs elsewhere.

Only repeated, score-aligned evidence may be promoted to Bill Evans Legend
Intelligence.
