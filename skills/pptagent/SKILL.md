---
name: pptagent
description: Create and revise editable PowerPoint presentations from a brief using HTML slide sources, rendering, and visual review. Use when the requested deliverable is a PPTX deck. The host authors the slides; text-only hosts can use an external visual reviewer.
---

# PPTAgent

Keep research and slide authoring in the host agent. The CLI handles
rendering, editable conversion, and verification that the delivered PPTX
matches the reviewed sources.

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

New tasks use the paper profile. Follow the user's page count; otherwise,
start with eight to ten pages.
Read [references/paper-presentation.md](references/paper-presentation.md).
Extract the supplied template's typography, header, spacing, and palette;
adapt the generic starter to it and keep a white or transparent background.
Explain the research problem, how the method works, and what the experiments
show. Use examples to explain difficult steps and describe what readers should
learn from each figure. State important conditions alongside the result or
operation they apply to.

Review every full-size exported page. First restate the argument without the
paper, then check it against the source. Put useful findings and fixes in the
normal deck-review record. Follow the task contract for fonts and target
software. Keep private templates and source assets outside the repo, and
omit added lower-left figure/page labels. Use `--profile general` for a
non-paper presentation.

## Create or revise

- Resolve the user's audience, message, page count, language, and aspect ratio.
  For a new workspace, run `init --workspace "$PWD" --slides N`, with optional
  `--profile paper|general`, `--aspect-ratio 16:9|4:3|A1`, `--language`, and
  `--font-family "Template Body Font"`. Existing tasks use `task.json`.
- Use available research tools as needed and preserve sources for checkable
  claims. Use a manuscript or asset manifest when it helps organize a complex
  deck.
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
  changes require fresh renders, reviews, and a build. After shared-resource
  changes, review all slides again.
- Run `finalize`. Deliver `answer.pptx` only when `complete=true`. If the user
  explicitly accepts an incomplete draft, set `delivery.mode: best-effort`;
  `delivery_ready=true` then permits delivery with the failed checks disclosed.

Commands take `--workspace` with an absolute path and emit JSON. Use `--help`
for arguments. A successful delivery includes a current `final-report.json`.
`complete` describes the recorded workflow. Keep API keys in environment
variables or the skill's `.env`, outside artifacts.
