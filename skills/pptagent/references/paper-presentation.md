# Reader-centered paper presentations

This fork defaults to academic paper presentations. Use the supplied
institutional template's cover, header, palette, and visual identity. The body
layout should adapt to the explanation, not reproduce a fixed split on every
page. Keep the background pure white or transparent. Keep the original
institutional template, artwork, and paper assets in the private task workspace,
not in this public repository. Do not modify or publish to the upstream repo.

## Explain the paper, not its table of contents

Follow the paper's overall progression: establish the background and problem,
explain why it matters, introduce the approach, show evidence, and discuss what
it means. Cover the important ideas across its major sections, without giving
every subsection its own title or slide. Synthesize adjacent material and use
concise descriptive titles that make the explanation clear. Exact source
headings, numbering, and a one-to-one section-to-slide mapping are not required.

Before outlining, identify the essential ideas and how they depend on each
other. Introduce unfamiliar objects, terminology, and the task before the
mechanism that uses them. Background and motivation need enough detail for a
reader who has not read the paper. A source figure from a later section may
appear early when it is the clearest way to establish the problem. Do not
place figures together merely because they share a section number.

Keep a private source map for checkable claims and a list of key topics covered
in the deck. A section reference is provenance, not a rule about slide order.
Explain important omissions rather than silently omit essential assumptions,
implementation details, experimental conditions, or conclusions.

## Information and layouts

Use enough concrete explanation to make the argument understandable. Prefer
problem settings, examples, assumptions, method steps, conditions, and
interpretation over slogans or isolated labels. Summarize and connect ideas;
adding words is not a substitute for explaining them. Never add repetition or
shrink text merely to meet a count. A short text-only page is valid when the
source and its role call for one.

The earlier 1.5–2 times body-text goal is not a per-slide acceptance rule.
Optional measurements may help compare revisions, but page regrouping makes
simple ratios misleading. Report a comparable baseline honestly when useful;
no ratio or exception form is required to justify a good explanation.

Choose the body layout for the content. Options include a full-width annotated
figure, a short explanation above a diagram, a sequence of steps, compact
comparison panels, and a text-led synthesis page. Two columns are an option,
not the default for every page. Avoid repetitive half-and-half compositions.
Keep the template identity consistent while varying useful body arrangements.

Aim for about eight to ten slides, but do not omit key evidence or compress
figures beyond readability to satisfy a rigid count. The page budget is a
planning aid. Figure-heavy experiments should use compact groups where the
comparisons remain readable; there is no mandatory two-page experimental cap.
Prefer fewer readable experimental pages over one figure per page, and prefer
an additional readable page over an illegible collage.

## Figures and academic style

Use original paper figures where they help explain a specific point. A reader
must know what to look at and why it matters. Preserve meaningful axes,
legends, code, and labels. A tiny original figure is not useful coverage: crop
only an appropriate detail with context, summarize with a faithful explanation,
or give it more room. Retain a private figure inventory and omission reasons.

Use restrained template colors, dark text, simple typography, and clear
hierarchy. Avoid gradients, saturated decorative cards, ornamental icons,
promotional language, or generic AI-style claims. No lower-left figure-number,
source-page, or slide-number labels. Keep source mappings in speaker notes or
the private asset manifest; preserve useful labels within original artwork.

## Read as a first-time reader before delivery

Review the rendered deck without leaning on what the author already knows.
Do this after authoring and again after material changes. Prefer an independent
reader when available. Record specific problems and the changes made, not a
blanket assertion that the deck looks fine. Check:

- Can the reader identify the objects being studied, the task, and the problem?
- Do background and motivation explain why the approach is needed?
- Are terms introduced before use, and does each major transition make sense?
- Can the reader explain the method and interpret the reported evidence?
- Are assumptions, conditions, limits, and important source topics covered?
- Does each figure have a readable scale and an explicit explanatory purpose?
- Does the layout help this page rather than repeat a convenient template?
- Is anything confusing when the reader lacks the paper and speaker notes?

Verify source claims separately. Reader review is not a license to invent
facts, inflate conclusions, or substitute aesthetic confidence for coverage.

## Audit and review evidence

`paper-plan.json` records the outline, source map, key-topic coverage, and
optional quantitative comparisons. Run:

```bash
python scripts/pptagent.py audit-paper --workspace /absolute/task \
  --plan /absolute/task/paper-plan.json --pptx /absolute/task/answer.pptx
```

The v2 audit checks what code can establish: actual slide count, declared
visible title/body text, duplicate text counting, source-map references, and
simple lower-left labels. It reports page count, density, narrative-stage, and
layout considerations as advisory information. It does not require literal
chapter headings, consecutive subsection references, fixed layouts, density
ratios, or a mandatory experimental-page count.

The audit cannot determine whether the reader understands the paper, whether
a summary is accurate, or whether coverage is sufficient. `ok` means only that
the deterministic checks passed. Coverage mappings remain author declarations,
not automatic proof. Human source review and full-size visual inspection remain
necessary, including grouped or inherited footer shapes.

After the reader review, record `reader_review` with the final PPTX's
`artifact_sha256`, reviewer description, concrete `findings` and changes,
`coverage_notes`, and `remaining_issues`. A current record establishes only
that the review evidence refers to this artifact; the software does not judge
the review's quality. `finalize` requires current reader-review evidence as well
as the existing visual/build checks. Unresolved reader-review issues must be
addressed before a complete delivery. Changing authored plan content invalidates normal render/build evidence.
The artifact-bound `reader_review` field is excluded from source hashing, so
recording the review after export does not trigger a circular rebuild.

See `paper-plan.example.json`. Legacy fields such as `section_ids`,
`baseline_body_units`, and `density_exception` remain readable for existing
workspaces, but they no longer impose the rejected hard rules.
