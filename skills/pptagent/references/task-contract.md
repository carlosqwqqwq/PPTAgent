# Task and source contract

Keep the task workspace separate from the skill:

```text
task.json                 slides, aspect_ratio, language; optional profile, font_family
slides/slideNN.html        editable slide sources, numbered from 1
assets/                   local images, CSS, fonts, and other resources
qa/                       generated renders and contact sheets
workspace-state.json      render, review, and build evidence (CLI-managed)
answer.pptx                editable deliverable
final-report.json          latest acceptance result
```

Supported canvases are `16:9` (1280x720), `4:3` (960x720), and `A1`
(2244x3178). Use `init` to create a task or write `task.json` directly:

```json
{"slides": 5, "aspect_ratio": "16:9", "language": "zh"}
```

All render dependencies must be local under `assets/` or `slides/`; use
relative paths. Download remote images before authoring. Ordinary hyperlinks
may point to websites. CSS and scripts can be inline. Shared resources are
hashed together, so changing any of them invalidates all slide reviews.
Let the CLI manage the render and review evidence.

The converter supports static HTML/CSS. The body must resolve to the requested
pixel dimensions in its default 1280x720 browser viewport; explicit dimensions
in inline or local CSS are the simplest choice. Prefer `p`, `h1`–`h6`, or list elements for text;
put backgrounds, borders, and shadows on wrapping `div` elements. Keep each
text element's content on one source line, since export can preserve newlines
that a browser collapses. The scaffold demonstrates these constraints.

Give positioned text containers an explicit width with spare room, especially
for mixed Chinese/Latin headings. Preserve template fonts when installed and
supporting the deck's languages and symbols. Otherwise, choose an available
substitute with suitable glyphs and similar style. When the user specifies
separate Chinese and Latin fonts, apply each through text styles or spans;
a fallback stack selects available glyphs rather than assigning fonts by
language. The starter includes CJK fallbacks; check the actual font selected
by the renderer.

Inspect the exported deck as well as the HTML previews. CLI page images use
LibreOffice. When the intended software, such as PowerPoint or WPS, is
available, open the final PPTX there and inspect font substitution, wrapping,
clipping, alignment, formulas, and figures. Record the software inspected and
any unavailable target in the normal review summary. Recheck affected pages
after font or export changes.

Research notes and a manuscript are optional working aids. Keep provenance for
externally checkable claims and reused assets in a form suited to the task.
Revise existing content when the user asks, including after an earlier build.


For this fork, `init` defaults to `profile: paper` and eight slides. Read
[paper-presentation.md](paper-presentation.md). `paper-plan.json` is an optional
outline/source map. `audit-paper` reads the actual PPTX and compares any
declared title/body text. Planning-note edits preserve unchanged renders;
edits to HTML and render resources use fresh exports and reviews.
`finalize` reruns the audit with the current plan, when present. The normal
exported-deck review records visual and reader-review findings together.
Older contact-sheet-only deck reviews need a fresh `review-deck` run so every
full-size page is included. General legacy tasks without `profile` retain their
authoring workflow.
