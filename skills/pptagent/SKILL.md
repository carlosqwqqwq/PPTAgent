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

New tasks use the paper profile: the supplied institutional template, a white
or transparent background, and an eight-to-ten-page planning target. Read
[references/paper-presentation.md](references/paper-presentation.md) first.
Follow the paper's overall narrative and cover its key ideas. Use synthesized,
descriptive titles rather than mandatory chapter headings or subsection labels.
Build sufficient background and motivation, and use figures where they clarify
the explanation, including earlier than their source section when useful.
Choose layouts for each page's content; do not force every page into two halves.
Text counts and experimental-page budgets are advisory, not quality gates.
Explain the core method in execution order, make quantitative claims
interpretable, and give figures a reading entry point while preserving their
scientific encoding. Separate the paper's conclusions from presenter analysis.
Before delivery, review from a first-time reader's perspective by restating
what the method does and what the evidence supports. Record specific problems
and fixes, and recheck the revised exported deck.
Check fonts and target-software compatibility, disclosing any unverified
target. The CLI cannot automatically judge comprehension or compatibility.
Keep private template artwork out of the repo and omit lower-left page labels.
Use `--profile general` only for a non-paper presentation.

## Create or revise

- Resolve the user's audience, message, page count, language, and aspect ratio.
  For a new workspace, run `init --workspace "$PWD" --slides N`, with optional
  `--profile paper|general`, `--aspect-ratio 16:9|4:3|A1` and `--language`. Existing tasks use `task.json`.
- Use available research tools as needed and preserve sources for checkable
  claims. A manuscript or asset manifest is useful for complex decks, not a
  prerequisite for every edit.
- Use `scaffold` if starter HTML is useful; it preserves existing slides.
  Author exactly the requested page count and replace the starter text.
- Run `review-slides`, inspect every returned image, then record each result:

```bash
"$SKILL_PYTHON" "$SKILL_ROOT/scripts/pptagent.py" record-slide-review   --workspace "$PWD" --slide slides/slide01.html --verdict pass   --summary "Readable; no clipping, overlap, or broken images."
```

- Run `build`, then `review-deck`. Inspect the exported deck's contact sheets;
  open full-size pages for dense content. Record `record-deck-review` with
  `--verdict` and `--summary`. Text mode records visual results automatically.
- Fix issues that affect the user's requirements or visible quality. Source
  changes require fresh renders, reviews, and a build. Shared resource changes
  invalidate all slide reviews. Rendering alone does not establish a pass.
- Run `finalize`. Deliver `answer.pptx` only when `complete=true`. If the user
  explicitly accepts an incomplete draft, set `delivery.mode: best-effort`;
  `delivery_ready=true` then permits delivery with the failed checks disclosed.

Commands take `--workspace` with an absolute path and emit JSON. Use `--help`
for arguments. A successful delivery includes a current `final-report.json`.
Keep API keys in environment variables or the skill's `.env`, outside artifacts.
