---
name: pptagent
description: Create and revise editable PowerPoint presentations from a brief using HTML slide sources, rendering, and visual review. Use when the requested deliverable is a PPTX deck. The host authors the slides; text-only hosts can use an external visual reviewer.
---

# PPTAgent

Use the host agent to research and author slides. The CLI handles rendering,
editable conversion, and verification that the delivered PPTX matches the
reviewed sources. Do not start another authoring agent.

## Setup

Resolve `SKILL_ROOT` to this directory. Use its `.venv/bin/python` when present,
otherwise an activated Python 3.11+ environment with the dependencies installed.
Set `SKILL_PYTHON` to that interpreter and run:

```bash
"$SKILL_PYTHON" "$SKILL_ROOT/scripts/pptagent.py" doctor --workspace "$PWD"
```

Read [references/task-contract.md](references/task-contract.md) for file layout
and HTML conversion constraints. The default `mode: multimodal` uses the host's
image viewer. Only for `mode: text`, read [references/text.md](references/text.md).
When `review_slides` and `review_deck` MCP tools are available in text mode, use
them for the corresponding review steps. Configuration is optional; defaults
live in `config.example.yaml`.

## Paper presentation profile

New tasks use the paper profile, with an eight-to-ten-page planning target.
Read [references/paper-presentation.md](references/paper-presentation.md).
Extract the supplied template's typography, header, spacing, and palette;
the bundled starter is generic and does not import a PPTX template.
Explain the problem and motivation, then the mechanism in execution order,
then the evidence and limits. Allocate space to the reasoning rather than
repeat a fixed layout. Keep quantitative claims interpretable and give figures
a reading entry point. Text counts and page budgets are planning aids.

Review every full-size exported page. First restate the argument without the
paper, then check it against the source. Put useful findings and fixes in the
normal deck-review record. Check fonts and the intended presentation software
when available; the CLI's LibreOffice renders do not establish another app's
compatibility. Keep private templates and source assets outside the repo, and
omit added lower-left figure/page labels. Use `--profile general` for a
non-paper presentation.

## Create or revise

- Resolve the user's audience, message, page count, language, and aspect ratio.
  For a new workspace, run `init --workspace "$PWD" --slides N`, with optional
  `--profile paper|general`, `--aspect-ratio 16:9|4:3|A1`, `--language`, and
  `--font-family "Template Body Font"`. Existing tasks use `task.json`.
- Use available research tools as needed and preserve sources for checkable
  claims. A manuscript or asset manifest is useful for complex decks, not a
  prerequisite for every edit.
- Use `scaffold` if starter HTML is useful; it preserves existing slides.
  Author exactly the requested page count and replace the starter text.
- Run `review-slides`, inspect every returned image, then record each result:

```bash
"$SKILL_PYTHON" "$SKILL_ROOT/scripts/pptagent.py" record-slide-review   --workspace "$PWD" --slide slides/slide01.html --verdict pass   --summary "Describe what was inspected and any fixes or remaining issues."
```

- Run `build`, then `review-deck`. Inspect every returned full-size page, then
  use contact sheets for sequence and consistency. Record `record-deck-review`
  with `--verdict` and `--summary`. Text mode combines full-page and overview
  visual results automatically; the author still verifies source accuracy.
- Fix issues that affect the user's requirements or visible quality. Source
  changes require fresh renders, reviews, and a build. Shared resource changes
  invalidate all slide reviews. Rendering alone does not establish a pass.
- Run `finalize`. Deliver `answer.pptx` only when `complete=true`. If the user
  explicitly accepts an incomplete draft, set `delivery.mode: best-effort`;
  `delivery_ready=true` then permits delivery with the failed checks disclosed.

Commands take `--workspace` with an absolute path and emit JSON. Use `--help`
for arguments. A successful delivery includes a current `final-report.json`.
`complete` describes the recorded workflow, not an automatic judgment of
comprehension or target-application compatibility. Keep API keys in environment
variables or the skill's `.env`, outside artifacts.

