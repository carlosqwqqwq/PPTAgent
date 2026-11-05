# Reader-centered paper presentations

Explain the paper to someone who has not read it. Start with the supplied
institutional template, keep a white or transparent background, and adapt the
body layout to the material. Keep private papers, template files, and artwork
in the task workspace, outside this repository.

## Start from the template and the argument

Inspect the template's cover, header, title/body fonts, text area, palette, and
spacing, then carry those choices into the HTML. Adapt the bundled generic
starter to the supplied template. Use `init --font-family "Template Body Font"`
to set its body font, and slide CSS for a distinct heading font. `scaffold`
preserves existing slides.

Read the whole paper before allocating pages. Identify the problem, why the
existing approach is insufficient, the core mechanism, the evidence, and the
limits. Introduce unfamiliar objects and terms before using them. Arrange the
argument in the order the audience needs to understand it. Use descriptive
titles and bring a later source figure forward when it explains the motivation
better. Keep a private source map for claims and reused figures.

Follow the user's requested page count. Otherwise, start with about eight to
ten slides and allocate space to the explanation. Give background and
motivation enough room to make the method understandable. A difficult
mechanism may need a worked example and a second page; related experiments
can share a page when their labels remain readable.

## Explain what happens and why

Follow a representative input through the method in execution order. Explain
what is being processed, how the state changes, why each operation helps, and
what the output means. Connect the components with complete sentences that
make the causal links clear. Keep the intermediate steps needed to understand
the method in the slide body.

For iterative methods, show how one round changes the state and affects the
next round. For selection or sampling, walk through a concrete candidate,
the quantities used to evaluate it, the decision rule, and the resulting state.
Use a worked example or annotated sequence to make an abstract rule tangible.
State essential conditions concisely beside the operation or conclusion they
qualify.

Give each page a clear teaching point and shape the layout around it: a large
annotated figure, a sequence with explanations, a compact comparison, or a
text-led synthesis. Use open space to explain a missing causal link, develop
a useful example, or enlarge the figure the audience needs to read. Keep
whitespace that separates ideas. When a page feels thin or difficult, rework
its explanation and composition together. Choose the amount of text and the
layout that make this particular point understandable.

## Explain what the evidence means

Make the question each experiment answers clear. Identify what was
compared, the metric and unit, the baseline, and the setting or budget needed
to interpret the result. Explain the meaningful difference and what it shows
about the method. For defect-finding results, lead with the important failure
and its consequence, using counts as supporting evidence.

Label totals, per-run results, means, maxima, and distinct findings precisely.
Include denominators, aggregation, and uncertainty where they affect the
conclusion. Distinguish measured findings from presenter interpretation or
proposed extensions when needed. State the finding directly and keep its
relevant scope or limitation close to it.

Use original figures where they explain a point. Guide the audience to the
relevant panel, axis, series, or comparison, then explain the pattern and its
meaning. Preserve useful labels, axes, legends, code, and scientific
color/line/marker meanings. Keep data and series mapping faithful in redraws
and retain the context needed to interpret a crop. Record important omissions
in the private source map.

Use dark text, clear hierarchy, and restrained template colors, without
decorative cards or promotional slogans. Enlarge or reorganize figures until
their important details are readable at presentation size. Keep added labels
beside the content they explain, leaving the lower-left corner free of added
figure, page, or source labels. Preserve meaningful labels inside original
figures.

## Review and revise the exported deck

Use HTML previews while authoring. After export, inspect every full-size page
for text, wrapping, clipping, formulas, alignment, images, and figure labels.
Use contact sheets to review the sequence and visual consistency. Text mode
combines the full-page and overview results into the normal deck review.

Read the deck first without the paper or author notes, preferably with an
independent reader. Restate the problem, method, and evidence in ordinary
words and identify missing terms, steps, or connections. Then check that
explanation against the paper's method, figures, results, and conditions.
Revise the pages so the argument is both clear and accurate.

Reread changed pages and adjacent transitions in the new export; reread the
full argument after material changes. Put the useful findings and fixes in
the existing `record-deck-review --summary` and issues. The visual reviewer
inspects the slides; the author checks the explanation against the paper.
Follow [task-contract.md](task-contract.md) for fonts and target-software review.

## Optional structural audit

`audit-paper` reads the actual PPTX. An optional `paper-plan.json` can hold an
outline, source/topic/figure mapping, and comparable revision measurements:

```bash
python scripts/pptagent.py audit-paper --workspace /absolute/task
```

Use its extracted text, text-unit counts, and declared-title/body comparisons
to inspect the deck's structure. Page budgets, layout repetition, narrative
transitions, and suspected lower-left labels are advisory. Assess figure
visibility, explanation, and source accuracy in the exported-page review.

Planning-note edits preserve unchanged slide renders. `audit-paper` and
`finalize` read the current plan; HTML, CSS, assets, and render-affecting task
changes use fresh exports and reviews. Existing `reader_review` notes remain
optional; use the normal deck record for final findings. See
`paper-plan.example.json` for a small example.
