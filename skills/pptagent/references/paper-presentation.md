# Reader-centered paper presentations

Explain the paper to someone who has not read it. Start with the supplied
institutional template, keep a white or transparent background, and adapt the
body layout to the material. Keep private papers, template files, and artwork
in the task workspace, outside this repository.

## Start from the template and the argument

Inspect the template's cover, header, title/body fonts, text area, palette, and
spacing before authoring. Carry those choices into the HTML. The bundled paper
starter is a generic example, not an imported institutional template. It starts
with a single-column explanation; its optional figure layout is one choice.
Use `init --font-family "Template Body Font"` to place the supplied font first
in the starter's font stack. Set distinct heading fonts in the slide CSS when
the template uses them. `scaffold` preserves existing slides.

Read the whole paper before allocating pages. Identify the problem, why the
existing approach is insufficient, the core mechanism, the evidence, and the
limits. Introduce unfamiliar objects and terms before using them. Follow these
dependencies rather than reproduce the table of contents. Use descriptive
page titles and bring a later source figure forward when it explains the
motivation better. Keep a private source map for claims and reused figures.

About eight to ten slides is a starting point. Assign space according to the
explanation: a difficult mechanism may need a worked example and a second
page; a simple comparison may fit beside its evidence. Background and
motivation must establish enough context to make the method understandable.
Combine related experiments where labels remain readable. Add a page when
that is clearer than compressing figures or omitting an essential step.

## Explain what happens and why

Show a representative input moving through the method in execution order.
Explain the objects or state, the important operations, why each operation is
useful, the conditions that must hold, and what the output means. Where the
method compares, filters, or stops, name the quantities and decision rule.
Distinguish preparation, generation, filtering, and evaluation when the paper
uses them; show loops and dependencies when they matter.

Use the detail that makes the mechanism reconstructable. A page that names
three components still needs to explain how they interact. Replace vague
phrases such as "an efficient, robust framework" with the actual operation and
its consequence. A running example, annotated diagram, or short paragraph can
supply that connection. Put essential explanation on the slide, not only in
speaker notes. These are writing questions, not mandatory fields or headings.

Allocate the page to its job: explanation above a diagram, a large annotated
figure, a sequence of steps, a compact comparison, or a text-led synthesis.
Two columns are useful when the two parts relate; they are not a default for
every page. Match the amount and placement of information to the reasoning,
not to a repeated card layout. Do not pad a short page or shrink a long one to
hit a count. Optional text-unit comparisons describe revisions; they do not
measure explanation quality, and regrouped pages may not be comparable.

## Make evidence interpretable

For an important result, identify what was counted or compared, the metric and
unit, the baseline, and the relevant setting or budget. Explain denominators
and aggregation when they change the meaning. Keep totals, per-run results,
means, maxima, and distinct findings separate. A larger count alone does not
establish broader coverage or greater efficiency. Preserve the source's
uncertainty and limitations; leave unavailable details unspecified.

Distinguish the paper's measured results and conclusions from presenter
analysis or proposed extensions where the distinction matters. Use ordinary,
specific wording, not a disclaimer before every sentence. Keep qualifications
next to the claim they affect.

Use original figures where they explain a point. Give the reader an entry:
which panel, axis, series, or comparison to inspect, what pattern matters, and
what it supports. A figure name alone is not an explanation. Preserve useful
labels, axes, legends, code, and scientific color/line/marker meanings. The
template palette applies to added presentation elements, not blanket
recoloring of source data. A faithful redraw must preserve the data and series
mapping. Crop only when the relevant context and conditions remain clear.

Inspect each figure in the exported page at presentation size. An asset in a
folder, a figure ID in a plan, or an image object in PPTX XML does not establish
that the figure is visible or readable. Enlarge or reorganize it when needed.
Record important omissions in the private source map. Keep added styling
restrained: dark text, simple hierarchy, template colors, no decorative cards
or promotional slogans. Omit added lower-left figure/page/source labels;
preserve meaningful labels inside original figures and chart axes.

## Review the exported deck

Use HTML previews while authoring. After export, inspect **every full-size
page** for actual text, wrapping, clipping, formulas, alignment, images, and
figure labels. Contact sheets help compare flow and consistency but cannot
replace this page-level inspection. Text mode checks each full-size page and
then the contact sheets, combining the results into one deck review.

First read the exported deck without the paper or author notes. Prefer an
independent reader when available. Restate the problem, method, and evidence
in ordinary words; note where a term, step, transition, or interpretation is
missing. Then open the paper and check that restatement against the original
method, figures, results, conditions, and limitations. This second pass catches
an explanation that is easy to follow but wrong or incomplete.

Fix the actual gaps. Reread changed pages and adjacent transitions in the new
export; reread the full argument after material changes. Record the important
findings and fixes in the existing final `record-deck-review --summary` and
issues. No extra comprehension score or sign-off form is needed. The external
visual reviewer sees slides, not the source paper; the author still performs
the source check. A visual pass is not a claim that source accuracy was
verified automatically.

Preserve template fonts where they are available and support the deck's
languages and symbols. The starter adds explicit CJK fallbacks, but those
fonts still need to be installed. Check the actual font selected by the
renderer, not only the first CSS family name. If a template font is missing,
choose an available substitute with suitable glyphs and similar style, then
recheck layout. HTML font fallback does not guarantee another app's fallback.

The CLI's exported images use LibreOffice. When PowerPoint, WPS, or another
application is the delivery target, open the final PPTX there when available
and inspect substitution, mixed Chinese/Latin wrapping, formulas, and figures.
Record the software actually inspected and any untested target in the review
summary. Recheck after font or export changes.

## Optional structural audit

`audit-paper` reads the actual PPTX. An optional `paper-plan.json` can hold an
outline, source/topic/figure mapping, and comparable revision measurements:

```bash
python scripts/pptagent.py audit-paper --workspace /absolute/task
```

The report includes extracted text and text-unit counts for every slide, even
when it is absent from the plan. If title/body text is declared, the audit
checks its presence and avoids counting the same text span twice. Extracted
XML may include hidden or off-slide text; picture counts omit some inherited
or drawn figures. Neither is a visibility or coverage score. Figure/topic
mappings remain declarations for review.

Page budgets, layout repetition, narrative transitions, and suspected
lower-left labels are advisory. A numeric chart label near the corner is not
a structural failure. `ok` means only that the structural comparisons passed.
The final report distinguishes those checks from the recorded visual judgment
and does not infer target-application compatibility.

The plan is not a rendering input. Editing notes or source mappings does not
invalidate unchanged slide renders, but `audit-paper` and `finalize` reread the
current plan. HTML, CSS, assets, and render-affecting task changes still need
fresh export/review evidence. Existing `reader_review` records remain readable
as optional artifact-bound notes; final review uses the normal deck record.
See `paper-plan.example.json` for a small example, not a required form.
