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

Read the paper in full before outlining the slides. Identify the research
problem, the limitations of existing approaches, how the proposed method
works, and what the evaluation shows, including its limitations. Define
unfamiliar terms and symbols when they first appear. Explain what important
quantities measure and how the method uses them. Order the slides so readers have the context needed
for each new idea. Use descriptive titles. A figure can appear earlier than
in the paper if it helps explain the problem. Keep a private record of the
sources for claims and figures.

Follow the user's requested page count. Otherwise, start with about eight to
ten slides. Include enough background for readers to understand why the
method is needed. A complex method may need a worked example on a separate
slide. Related experiments can share a slide when the figures and labels
remain readable.

## Explain what happens and why

Trace a representative input through the method. Describe the data or state
at each important step, the operation performed, and its effect on subsequent
steps. Explain why the method needs that operation, with a short sentence
beside the corresponding part of the figure. Describe the final output and
what it represents. Keep these explanations in the slide body.

For an iterative method, show what changes after one round, what remains
fixed, and how this affects the next round. Show which stored information is
updated and explain why. For selection or sampling, work through an example:
give the candidate's relevant values, apply the decision rule, and show the
result. State important conditions alongside the operation or conclusion
they apply to.

Choose a layout that suits the material, such as an annotated diagram, a
comparison, or a short explanation. Use text to explain relationships that
are difficult to see in the figure. Add an example where a step or rule needs
further explanation. Use spare room to enlarge figures with small labels or
details. Remove repeated text from crowded slides, and leave enough space
to distinguish separate ideas.

## Explain what the evidence means

State the question each experiment addresses. Introduce the baseline,
metrics, units, and experimental conditions needed to interpret the results.
Explain what the comparison shows about the proposed method. When metrics
change in different directions, explain what each measures and use the
paper's evidence to interpret the difference. When experiments have different
budgets or purposes, state these before relating their findings.

For an ablation, describe what changed between runs and how the results
changed. For a case analysis, show what each component did in the example.
A defect example should identify the expected and observed behavior, then
show which output or state reveals the error. Report how many defects were
found and describe the main types.

State whether a number is a total, a per-run result, an average, a maximum,
or a count of distinct findings. Explain denominators, aggregation, and
uncertainty when they affect the conclusion. Make clear which conclusions
come from the paper and which are the presenter's analysis or proposals.
State each finding directly, with any conditions needed to interpret it.

Use original figures when they help explain the paper. Point readers to the
relevant panel or comparison and explain what they should notice. Use the
same terms in the text and figure, explaining unfamiliar labels where needed.
Preserve labels, axes, legends, code, and the meaning of colors, lines, and
markers. Redrawn figures should preserve the data and series mapping. Crops
should retain the context needed to interpret the figure. Record important
omissions in the private source map.

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
