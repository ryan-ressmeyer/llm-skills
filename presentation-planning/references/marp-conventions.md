# Stage 4: Marp Conventions

Stage 4 produces `slides.md` — a Marp markdown file that converts the assertion list into a skeleton deck. The deck is a skeleton because actual figures and theme CSS are filled in later. The speaker notes, assertion titles, transitions, and structural build markers all come through from Stage 3.

---

## Marp basics

A Marp file is a markdown document with YAML frontmatter that enables Marp rendering. Slides are separated by horizontal rules (`---`). Marp supports directives (front-matter and per-slide), HTML comments as speaker notes, and standard markdown with a slide-aware CSS layer.

### Minimal frontmatter

```markdown
---
marp: true
theme: default
paginate: true
math: katex
---
```

| Directive | Purpose |
|-----------|---------|
| `marp: true` | Required — enables Marp rendering. |
| `theme: default` | Placeholder. A custom theme (light + dark pair) will be wired in later. |
| `paginate: true` | Page numbers. |
| `math: katex` | Enables KaTeX math rendering (for equations). |

Leave the theme as `default` in Stage 4. Custom theme CSS is a later concern.

### Per-slide directives

Marp allows per-slide configuration via HTML comments prefixed with an underscore:

```markdown
---
<!-- _class: dark -->       <!-- apply the "dark" class to this slide only -->
<!-- _backgroundColor: #000 -->
<!-- _color: #fff -->

# Fluorescence image slide
```

Use these sparingly during Stage 4. Specify classes only where Stage 3 called for them (e.g., a dark background for a microscopy slide).

---

## Speaker notes

**Marp renders HTML comments as presenter notes in presenter mode.** Use the comment form:

```markdown
## LGN receptive fields elongate along the saccade axis

![width:800px](figures/TODO-rf-anisotropy-scatter.png)

<!--
SPEAKER NOTES
- Along-axis / orthogonal extent ratio: ~1.4 across n=347 units.
- Pause after "along the saccade axis" — let it land.
- If asked "is this just motion smear?" point forward to Dive 3 passive-replay control.
-->
```

Lift speaker notes directly from Stage 3's `assertions.md`. Do not invent new ones.

---

## Slide structure template

Each slide in the skeleton has a consistent shape:

```markdown
---

## [Assertion title — full sentence from assertions.md]

![width:700px](figures/TODO-descriptive-name.png)

<!--
SPEAKER NOTES
- [note 1]
- [note 2]

TRANSITION IN: [one sentence from assertions.md]
TRANSITION OUT: [one sentence from assertions.md]
-->
```

### Why transitions live in speaker notes (not on-slide text)

Transitions are spoken, not read. Putting them on the slide duplicates what the speaker says and violates the "slide is not a teleprompter" rule. They belong in presenter-only notes.

---

## Figure placeholders

**Never invent figure content.** Use placeholder image paths the user can swap out:

```markdown
![width:700px](figures/TODO-rf-anisotropy-scatter.png)
```

Describe what the figure should contain in a comment directly below the placeholder, pulled from `assertions.md`:

```markdown
![width:700px](figures/TODO-rf-anisotropy-scatter.png)

<!--
FIGURE: scatter of along-axis vs. orthogonal RF extent for all 347 units.
Unity line dashed. Marginal histograms on both axes. Color by animal.
Most points lie above the unity line — that is the takeaway the audience
should see in ~2 seconds.
-->
```

### Figure directory convention

Create a `figures/` subdirectory next to `slides.md`. Place a `figures/README.md` listing each `TODO-*.png` filename and what the figure should be. This becomes the user's checklist of figures to produce.

---

## Progressive reveals (builds)

Marp's support for progressive reveals is weaker than Keynote/PowerPoint, but three patterns work:

### Pattern A — one-reveal-per-slide (simplest, always works)

Duplicate the slide, adding one element at a time. The audience sees a sequence of near-identical slides, each adding a panel. Use when the build has 2–4 stages.

```markdown
---

## The anisotropy emerges 30–50 ms after saccade onset

![width:700px](figures/TODO-anisotropy-timecourse-panel1.png)

<!-- BUILD: panel 1 — raw time course only -->

---

## The anisotropy emerges 30–50 ms after saccade onset

![width:700px](figures/TODO-anisotropy-timecourse-panel2.png)

<!-- BUILD: panel 2 — add shaded 95% CI -->
```

### Pattern B — CSS fragments (fewer slide duplicates)

Marp supports fragment-style reveal via a CSS class applied by the theme. Wait for the theme to be defined. For now, mark the intended build points with comments:

```markdown
---

## The anisotropy emerges 30–50 ms after saccade onset

![width:700px](figures/TODO-anisotropy-timecourse.png)

<!-- BUILD: reveal panel 2 (shaded CI) on advance -->
<!-- BUILD: reveal annotation arrows on next advance -->
```

The `BUILD:` comments are purely informational at Stage 4. They become real fragments when the theme is wired up or when the user swaps to Pattern A.

### Pattern C — pre-rendered animated figure

For figures where the animation is essential (e.g., a reconstructed eye trace moving across a scene), export as a short autoplay video or GIF. Marp renders MP4/GIF via standard image markdown:

```markdown
![width:700px](figures/TODO-eye-trace-animation.mp4)
```

Defer until the user's visual-elements tooling is integrated.

### Which to use

- Default to Pattern A for Stage 4 skeletons. It is robust and doesn't depend on theme CSS.
- Mark Pattern B sites with `BUILD:` comments for later CSS-driven builds.
- Flag Pattern C figures to the user so they know they need to pre-render.

---

## slides.md shape

```markdown
---
marp: true
theme: default
paginate: true
math: katex
---

# [Talk title]

## [Speaker name, affiliation, occasion]

<!--
SPEAKER NOTES
- Pause 2 seconds before first word.
- Open with ABT core statement (see storyline.md).
-->

---

## [Assertion 2 from assertions.md]

![width:700px](figures/TODO-figure-2.png)

<!--
SPEAKER NOTES
- [notes from assertions.md]

TRANSITION IN: [from assertions.md]
TRANSITION OUT: [from assertions.md]
-->

---

## [Assertion 3]

[...continue for all slides in assertions.md...]

---

## Summary

- [One-sentence recap of Dive 1 result]
- [One-sentence recap of Dive 2 result]
- [One-sentence recap of Dive 3 result]
- **[Restate ABT core statement]**

<!--
SPEAKER NOTES
- Leave this slide up for Q&A. Do NOT click forward to Acknowledgments.
- Do NOT say "thank you" or apologize. Pause, then sit down / take the first question.
-->

---

## Acknowledgments

[To be filled in.]

<!--
Click to this slide only after Q&A has wound down.
-->
```

---

## Rendering the skeleton

The user will render the deck themselves. Mention in the closing message:

> Render to PDF for a quick visual-hygiene pass (catches text overflow, sizing issues):
> ```
> npx @marp-team/marp-cli slides.md --pdf
> ```
>
> Render to HTML for actual delivery (preserves fragments and transitions):
> ```
> npx @marp-team/marp-cli slides.md --html
> ```

Do not attempt to render the deck yourself in Stage 4.

---

## Post-Stage-4 rehearsal suggestion

After writing `slides.md`, close with a **suggestion** (not a requirement):

> The skeleton is ready. The next productive step is to rehearse the talk aloud once, with the deck visible, speaking the transitions from the notes rather than reading them. Time it. Note any slide where you stumbled, any transition that felt forced, any moment where you wanted a slide you don't have.
>
> When you come back, use `presentation-editing` with your rehearsal notes in hand.

Do not block progress on rehearsal — the user will decide when they're ready.
