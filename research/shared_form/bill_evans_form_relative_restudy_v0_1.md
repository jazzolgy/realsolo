# Bill Evans Compilation — Form-Relative Restudy v0.1

## What changed

The previous album studies were useful for navigation but often asked questions
in recording-time coordinates:

- opening vs middle vs late
- 10% / 50% / 90% of track
- high-activity window at a timestamp

This restudy reinterprets the same evidence using musical position:

- core-form length
- current form bar
- section
- chorus/recurrence index
- performance phase
- non-core arrangement segment

The result changes several conclusions.

## 1. There is no single "jazz form length" in this corpus

The 24-track source contains, with varying confidence:

- 10-bar circular form: Blue In Green
- 12-bar minor blues: Israel
- 26-bar asymmetric form: You Must Believe In Spring
- many 32-bar standards
- 40-bar AABAC: In Your Own Sweet Way
- 56-bar AABA: Without A Song
- 64 notated bars: Alice In Wonderland
- 80-bar Waltz For Debby
- non-cyclic/ostinato material: Peace Piece
- long/asymmetric forms still requiring exact mapping

Therefore a drummer must not carry a hidden 8/32-bar assumption.

The minimum useful drummer navigation state is:

form_length
+ form_bar
+ chorus_index
+ performance_phase
+ arrangement_segment
+ distance_to_boundary

## 2. Earlier "middle expansion" is a narrative finding, not a form-bar rule

The 1000-pass study found broad opening restraint and frequent middle expansion.

Under the new model this must **not** become:
"play more around bars 13–20."

A recording may contain many complete choruses. The middle of the recording may
be bar 3, bar 17, or bar 31 of the current form.

The legitimate learning is:

- later performance phases often permit greater interaction;
- the same form bar may be realized more actively in a later chorus;
- performance narrative and form position are independent coordinates.

This is a much stronger model than normalized track position.

## 3. Setup/fill intelligence should be boundary-distance based

For drums, the useful question is not:
"Are we near the end of the recording?"

It is:
- how many bars/beats to the next section boundary?
- how many bars/beats to the end of the core form?
- is that boundary perceptually important?
- are we in head, solo, out-head, coda, or an inserted segment?

This explains why fills should sometimes appear every 8/16/32 bars and sometimes
not at all.

## 4. FORM KNOWLEDGE and FORM MARKING remain different

Blue In Green is the clearest counterexample to mechanical boundary marking.

Its 10-bar circular form has a weak/noncadential seam. A drummer can know the
exact top of form while deliberately avoiding a conspicuous fill/crash.

The model therefore needs both:
- boundary location/confidence
- boundary marking need/salience

## 5. Long forms require memory beyond the recent 8 bars

Waltz For Debby, Alice In Wonderland and Without A Song show why a drummer cannot
navigate only through local phrase memory.

Examples:
- Waltz For Debby: 80-bar head form plus meter/feel changes, tags and coda
- Alice In Wonderland: 64 notated bars with 16-bar A-section scale
- Without A Song: 56 bars, with a 16-16-8-16 structure

A local 4/8-bar pattern detector can sound convincing while being formally lost.

The drummer needs:
- core form length
- section identity
- form bar
- chorus index
- long-range boundary memory

## 6. Odd/asymmetric forms are not edge cases

You Must Believe In Spring is 26 bars (8+8+10).
In Your Own Sweet Way is 40 bars.
Blue In Green is 10.
Israel is 12.

These tracks show that "four 8-bar blocks" is a common archetype, not a universal
law.

The form engine must accept arbitrary positive bar counts and named/unnamed
section lengths.

## 7. Meter and form are independent

Waltz For Debby and In Your Own Sweet Way already show this.

A form can remain identifiable while:
- head and solo use different felt pulse
- meter/feel shifts
- time responsibility moves between players

Therefore:
form_bar does not determine ride pattern.
It only tells the drummer where they are.

## 8. Arrangement segments need their own memory

The corpus contains or plausibly contains:
- rubato intro
- arranged intro
- vamp
- tag
- solo break
- interlude/open solo area
- D.C./D.S. navigation
- coda
- outro

These are not errors around the core form.

They are first-class arrangement segments.

A drummer should be able to hold:
"core form is paused; currently in interlude/vamp"
and later re-enter the recurring form at a verified location.

## 9. Same-position comparison becomes the main learning experiment

The most valuable question is now:

"At the same musical location, what changes with context?"

For Autumn Leaves:
A1 bar 5 on head
vs A1 bar 5 on piano solo chorus 1
vs A1 bar 5 on later chorus
vs A1 bar 5 on out-head.

Compare:
- piano foreground density
- bass time/counterline role
- drum time surface
- snare/kick activity
- accent and note body
- response delay
- register/orchestration
- motif reuse
- boundary preparation

That directly separates:
- tune requirement
- form-position requirement
- current ensemble role
- player-specific tendency
- one-off event

## 10. What the existing mixed-audio data is now good for

Existing onset/RMS/spectral/low-band data remains useful, but its status changes.

It is a **navigation layer**:
- find unusual texture change
- find density expansion/contraction
- locate candidate handoffs
- locate possible solo/drum-forward regions

It becomes musical evidence only after:
timestamp
→ arrangement segment
→ form/section/bar
→ instrument/ensemble attribution.

## 11. New drummer model implied by the restudy

For basic competent drumming, exact harmony is helpful but not always necessary.

A surprisingly useful minimum state is:

- meter / felt pulse
- core form length
- current form bar
- section if known
- chorus index
- distance to section/form end
- performance phase
- arrangement segment
- current foreground owner
- boundary marking need

Harmony and melody then refine:
- setups
- ensemble figures
- comping dialogue
- accent targets
- phrase-specific interaction.

This supports the project owner's observation:
**if the drummer knows where the bars are in the form, the drummer can already
perform coherently even when the full score is unavailable.**

## 12. Cross-instrument consequence

The same coordinate benefits every player, but the dependency differs.

Drums:
form position can already drive strong navigation and pacing.

Bass:
form position + harmony greatly improves route and arrival decisions.

Piano/Sax:
form position + harmony/melody gives phrase target and development context.

Therefore form location belongs to Shared Music Intelligence, not to any one
Player.

## Immediate research order

1. Complete Autumn Leaves at bar-level across several choruses.
2. Apply form-cycle alignment to all high-confidence 32-bar tracks.
3. Handle Blue In Green separately as a 10-bar circular-form benchmark.
4. Use Israel as the 12-bar benchmark.
5. Use You Must Believe In Spring and In Your Own Sweet Way as asymmetric-form
   benchmarks.
6. Use Waltz For Debby / Alice In Wonderland / Without A Song as long-form
   memory benchmarks.
7. Keep Peri's Scope, B Minor Waltz, Gary's Theme and Re: Person I Knew in an
   uncertainty queue until exact recurring-form/arrangement maps are verified.

## Bottom line

The strongest new conclusion is:

**The drummer does not primarily need "song elapsed position." The drummer needs
a continuously maintained formal address.**

For many jazz situations that address can be as simple as:

"32-bar form, chorus 4, bar 29, 4 bars to top"

and that is already enough to make better decisions about space, setup,
continuity and re-entry than a much richer acoustic model that does not know
where it is in the form.
