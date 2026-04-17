# Stage 3: Assertion List — Per-Slide Rubric

Stage 3 produces `assertions.md`. For every slide in the eventual deck, this file specifies what the slide asserts, what proof it shows, what the speaker says around it, and what is easy to forget while delivering it. The file is still plain markdown — no Marp yet.

---

## The assertion-evidence unit

Every slide is one unit of argument. The unit has three parts:

1. **Assertion** — a complete declarative sentence stating the slide's takeaway, placed as the slide title.
2. **Evidence** — one visual (figure, schematic, photograph, code snippet, equation) that proves the assertion.
3. **Spoken frame** — what the speaker says on approach and on departure, plus the notes they need to remember in the moment.

If any of the three is missing, the slide is not done. If the evidence proves more than one assertion, the slide is two slides.

---

## The assertion (slide title)

**A declarative full sentence stating the conclusion.** Length: one line, ideally ≤ 10 words, never > 2 lines.

### Good

- *"LGN receptive fields elongate along the saccade axis during free viewing."*
- *"Protein X represses Gene Y in postmitotic neurons."*
- *"The custom Vulkan pipeline reduces stimulus latency to under 2 ms."*

### Bad (topical — fails Alley's test)

- *"LGN RF results"*
- *"Regulation of Gene Y"*
- *"Benchmarks"*

### Bad (hedged into meaninglessness)

- *"LGN RFs may be affected by saccades in some conditions."*
- *"Protein X is thought to potentially play a role in repressing Gene Y."*

### Bad (two assertions fused)

- *"We built a Vulkan pipeline and showed it reduces latency."* — split into two slides: one on the pipeline, one on the measurement.

---

## The visual

**One image per slide, chosen to prove exactly the assertion.** Describe it in prose in `assertions.md`; do not generate the image. The user supplies figures from their own analyses.

### What to specify

- What the figure shows (axes, panels, curves).
- What the audience should look at first.
- What annotations or highlights the figure needs (e.g., a box around the key panel, an arrow to the key feature).
- Whether progressive reveal is needed (if the figure has multiple panels or components introduced sequentially).

### Rules

- **If you will not explain it, delete it.** Every axis, label, and legend entry must correspond to something the speaker will say.
- **Never paste a published figure untouched.** Crop, relabel, recolor, and remove extraneous panels. The published figure was optimized for a reader with infinite time; the talk figure is optimized for a 60-second glance.
- **Build up complex figures.** A diagram with four components should appear as four sequential reveals, each introduced in speech.
- **No red-green pairs.** No 3D chart effects. No gridlines unless they carry meaning.

---

## The spoken frame

### Transition in

One sentence the speaker says **before** this slide's assertion is revealed. It is the bridge from the previous slide's result, phrased as a question or setup that the current slide answers.

> "So under passive fixation, the RFs look classical. What happens when the monkey is freely viewing?"

### Transition out

One sentence the speaker says **while moving to** the next slide. It both lands the current assertion and sets up the next.

> "The anisotropy is clear in one unit. Is it systematic across the population?"

Transitions are the glue that makes the talk feel like an argument rather than a recitation. In rehearsal, the speaker should be able to deliver each transition without looking at notes.

### Speaker notes

2–4 bullets of *what the speaker needs in the moment but wouldn't want to say out of rote memory*. Examples of what belongs:

- Specific numbers the speaker might misremember ("n = 347 units, 3 monkeys").
- Pre-empts for the skeptical question the speaker expects here ("if asked about retinal image motion, point to the passive-replay control in Dive 3").
- Reminders about pacing ("pause after 'is not a passive relay' — let it land").
- The specific phrasing for a hard-to-explain concept ("frame the anisotropy index as 'along-axis extent divided by orthogonal extent'").

Notes are **not** a script. They are what the speaker glances at while speaking.

---

## What assertions.md looks like

One table per slide, or a uniform list. Either is fine; consistency matters more than format.

```markdown
# Assertions — [Talk Title]

Total slides: [N]  |  Target duration: [T] min  |  Pace: ~[T/N] min/slide

---

## Slide 1 — Title
- **Assertion:** [core message as a single sentence, OR a title + speaker name if this is a pure title slide]
- **Visual:** [description]
- **Transition in:** —
- **Transition out:** [opening sentence of the talk]
- **Speaker notes:**
  - [Pause 2 seconds before speaking]
  - [...]

## Slide 2 — [assertion shortened]
- **Assertion:** [complete sentence]
- **Visual:** [description with axes, panels, annotations, and what the audience looks at first]
- **Transition in:** [one sentence]
- **Transition out:** [one sentence]
- **Speaker notes:**
  - [number to remember]
  - [skeptic pre-empt]
  - [pacing cue]

## Slide 3 — [...]
[...]
```

---

## Per-slide self-check

Before declaring a slide's assertion row done, verify:

- [ ] Title is a complete sentence stating a conclusion.
- [ ] One assertion per slide (no "and" joining two claims).
- [ ] Visual is specified well enough that the user can tell whether their existing figure fits or a new one is needed.
- [ ] Every axis/label/panel on the visual has a sentence the speaker will say about it. Otherwise, the element is cut or the slide is built progressively.
- [ ] Transitions in and out are single sentences.
- [ ] Speaker notes contain at least one of: a specific number, a skeptic pre-empt, or a pacing cue.
- [ ] The assertion is a step in the Storyline arc — trace it back to a dive or beat.

---

## Slide-count sanity check

Rough rule: **60–90 seconds per slide** for a technical talk, including transitions and pauses. A 30-minute talk is therefore ~20–30 slides, not 50.

If the assertion list is producing more slides than the time budget allows, the talk either has too many dives or individual dives are over-built. Revisit Storyline and prune.
