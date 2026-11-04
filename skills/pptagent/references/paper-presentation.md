# Paper presentation defaults

This fork defaults to academic paper presentations. Explicit task instructions
may change the page budget; a generic presentation uses `--profile general`.
The user's supplied institutional template is the layout source, not an
inspiration to replace with an independently designed deck. Keep its cover,
header, rules, margins, logo placement, and body proportions. Keep template
files and institutional artwork in the private task workspace, not this repo.

## Structure and titles

1. Extract the paper's numbered sections and subsections before outlining.
2. Follow their source order throughout the deck. Use their original headings
   or faithful translations as slide titles, retaining the section numbers.
3. A combined slide names the consecutive sections it covers. A repeated
   section may use a simple continuation label. Do not invent takeaway,
   rhetorical, promotional, or conclusion-style titles in place of headings.
4. Include implementation, discussion, related work, and conclusion when the
   paper has them. Compress adjacent sections rather than silently replace them.
5. Default to eight slides including the cover, with a ten-slide target.
   This is a budget, not a reason to omit necessary paper sections or evidence.

## Text density

For a revision, measure visible explanatory body text against the previous
deck, excluding titles, figure captions, axis labels, citations, and footers.
Target **1.5–2.0 times** the previous amount on each comparable content slide.
Do not satisfy the target by increasing speaker notes, repeating claims,
shrinking text until unreadable, or adding vague filler. Add concrete problem
settings, assumptions, method steps, experiment conditions, findings, and
interpretation already supported by the paper. Preserve usable body text size.

Record which previous slides form the comparison and how regrouping affects
it. Compare like-for-like material, not every new slide to the old deck-wide
average. A text-only section with little source material may remain shorter;
it does not need invented content or a decorative figure. The cover is exempt.
These exceptions do not excuse sparse method or experimental explanation.
If a specific target conflicts with legibility or source evidence, report the
actual ratio and reason rather than claim the numerical target passed.

## Figures and experimental pages

Use original paper figures wherever they convey useful evidence. Inventory
figures and tables, including intentional omissions and the reason. Do not
redraw scientific plots inaccurately or crop away meaningful legends and axes.
For figure-heavy experimental sections, first group related plots into compact
multi-panel pages, shrink proportionally, align edges, and remove unnecessary
whitespace. Use the fewest pages whose labels and comparisons remain readable.
Try two experimental pages for a ten-page deck, then verify at full size;
more pages require a documented readability or evidence reason. Experimental
plots must not crowd out the method, implementation, or discussion sections.

## Visual style and footer

Use a pure white or transparent background, subdued template blues and dark
text, restrained separators, and simple academic typography. No gradients,
saturated decorative cards, ornamental icons, large slogans, or AI-style
promotional prose. Text-only pages are valid when the paper section has no
figure. No lower-left figure number, source-page label, `p. N`, `Fig. N`, or
slide-number annotation. Keep source mappings in speaker notes or the private
asset manifest. Preserve meaningful labels inside original figure artwork.

## Acceptance

Use `paper-plan.json` to record the source order, approved translated titles,
body-text baseline, figure inventory, and experiment budget. Run:

```bash
python scripts/pptagent.py audit-paper --workspace /absolute/task \
  --plan /absolute/task/paper-plan.json --pptx /absolute/task/answer.pptx
```

The audit checks the actual PPTX text and positions, not merely the plan. It
checks sequence, title presence, declared body presence, text ratios, the page
budget, and visible lower-left labels. It does not prove that a translation is
faithful, that a declared baseline is correctly selected, or that every image
is readable. Inspect every rendered slide and the exported PPTX; record these
judgments separately. A numerical pass never replaces visual review.

The plan format is documented in `paper-plan.example.json`. `body` contains
only visible explanatory text, and `baseline_body_units` uses `text_units()`:
each CJK character is one unit; each Latin word or number token is one unit.
The baseline must come from the prior deck and its selection must be described
in `baseline_source` / `baseline_mapping`. `kind: text-only` or `cover` can carry
a short `density_exception`; it remains visible in the report. Normal content
slides with a missing or out-of-range baseline require correction or an
explicit source/readability-based `density_exception`. The report keeps the
measured ratio and `density_target_met` separate from that exception. No universal fixed word
count is imposed on new decks: omit `baseline_body_units` only with
`revision: false`. A paper plan is hashed into normal render/build evidence,
and `finalize` enforces the audit for the paper profile.

Numerical targets do not justify filler or illegible figures. A justified
`page_budget_reason` can exceed ten pages (`init --page-budget-reason`), and
`experiment_budget_exception` can exceed the planned experimental budget.
All exceptions remain listed for human review; they do not make an unmet
measurement pass. Continuation titles belong in section `title_variants`.
