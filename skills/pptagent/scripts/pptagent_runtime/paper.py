"""Extract paper-deck structure and compare optional planning notes."""

from __future__ import annotations

import hashlib
import json
import math
import posixpath
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}
UNITS = re.compile(
    r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]|[A-Za-z0-9]+(?:[.'’_-][A-Za-z0-9]+)*"
)
LABEL = r"(?:fig(?:ure)?\.?|图|p(?:age)?\.?|页|slide)\s*\d+(?:\s*[-–,]\s*\d+)*"
FOOTER = re.compile(
    rf"(?:source\s*[:：]\s*|来源\s*[:：]\s*)?{LABEL}(?:\s*[·|;/,]?\s*{LABEL})*",
    re.IGNORECASE,
)


def text_units(text: str) -> int:
    """Count CJK characters and Latin/number tokens, without punctuation."""
    return len(UNITS.findall(text))


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _slides(path: Path) -> tuple[list[dict[str, Any]], int, int]:
    with zipfile.ZipFile(path) as archive:
        presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
        size = presentation.find("p:sldSz", NS)
        if size is None:
            raise ValueError("PPTX has no slide size")
        width, height = int(size.attrib["cx"]), int(size.attrib["cy"])
        relationships = ET.fromstring(archive.read("ppt/_rels/presentation.xml.rels"))
        targets = {rel.attrib["Id"]: rel.attrib["Target"] for rel in relationships}
        relation_ns = (
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        )
        names = [
            posixpath.normpath(posixpath.join("ppt", targets[item.attrib[relation_ns]]))
            for item in presentation.findall("p:sldIdLst/p:sldId", NS)
        ]
        names = [name.lstrip("/") for name in names]
        slides = []
        for name in names:
            root = ET.fromstring(archive.read(name))
            shapes = []
            for shape in root.findall(".//p:sp", NS):
                paragraphs = [
                    "".join(t.text or "" for t in p.findall(".//a:t", NS))
                    for p in shape.findall(".//a:p", NS)
                ]
                text = "\n".join(paragraphs)
                offset = shape.find("p:spPr/a:xfrm/a:off", NS)
                shapes.append(
                    {
                        "text": text,
                        "x": int(offset.attrib["x"]) if offset is not None else None,
                        "y": int(offset.attrib["y"]) if offset is not None else None,
                    }
                )
            # Tables store text outside p:sp. XML presence does not establish visibility.
            full_text = "\n".join(
                "".join(t.text or "" for t in p.findall(".//a:t", NS))
                for p in root.findall(".//a:p", NS)
            )
            table_texts = [
                "".join(t.text or "" for t in p.findall(".//a:t", NS))
                for p in root.findall(".//p:graphicFrame//a:p", NS)
            ]
            slides.append(
                {
                    "shapes": shapes,
                    "text": full_text,
                    "table_texts": table_texts,
                    "picture_count": len(root.findall(".//p:pic", NS)),
                }
            )
    return slides, width, height


def _check_body(actual: dict[str, Any], title: str, body: list[str]) -> bool:
    remaining = [
        compact(shape["text"])
        for shape in actual["shapes"]
        if compact(shape["text"]) != title
    ]
    remaining.extend(compact(text) for text in actual["table_texts"])
    for declared in sorted((compact(text) for text in body), key=len, reverse=True):
        match = next(
            (
                i
                for i, region in enumerate(remaining)
                if declared and declared in region
            ),
            None,
        )
        if match is None:
            return False
        remaining[match] = remaining[match].replace(declared, "\0", 1)
    return True


def _reader_review(plan: dict[str, Any], artifact_hash: str) -> dict[str, Any]:
    review = plan.get("reader_review") or {}

    def nonempty_text(value: Any) -> bool:
        return isinstance(value, str) and bool(value.strip())

    findings = review.get("findings")
    recorded = bool(
        nonempty_text(review.get("reviewer"))
        and nonempty_text(review.get("coverage_notes"))
        and isinstance(findings, list)
        and all(
            isinstance(finding, dict)
            and nonempty_text(finding.get("problem"))
            and nonempty_text(finding.get("change"))
            for finding in findings
        )
        and isinstance(review.get("remaining_issues"), list)
    )
    return {
        "recorded": recorded,
        "current": recorded and review.get("artifact_sha256") == artifact_hash,
        "resolved": recorded and not review["remaining_issues"],
        "comprehension_verified_automatically": False,
        "evidence": review,
    }


def audit(
    plan_path: Path | None, pptx_path: Path, page_budget_reason: str = ""
) -> dict[str, Any]:
    plan = json.loads(plan_path.read_text(encoding="utf-8")) if plan_path else {}
    slides, width, height = _slides(pptx_path)
    planned = plan.get("slides", [])
    sections = plan.get("sections", [])
    section_ids = {section["id"] for section in sections}
    if len(section_ids) != len(sections):
        raise ValueError("source sections must have unique IDs")
    topics = plan.get("key_topics", [])
    topic_ids = {topic["id"] for topic in topics}
    if len(topic_ids) != len(topics):
        raise ValueError("key topics must have unique IDs")
    issues: list[str] = []
    warnings: list[str] = []
    if "slides" in plan and len(slides) != len(planned):
        issues.append(f"Plan has {len(planned)} slides; PPTX has {len(slides)}.")
    target = plan.get("max_slides")
    if target is not None and len(slides) > int(target):
        warnings.append(
            f"Deck has {len(slides)} slides; the planning target is {target}. "
            "Check whether the added pages support coverage or readability."
        )
    narrative_order = plan.get("narrative_order", [])
    stage_ranks = {stage: rank for rank, stage in enumerate(narrative_order)}
    last_stage = -1
    covered: set[str] = set()
    measurements = []
    layouts = []
    for number, actual in enumerate(slides, 1):
        entry = planned[number - 1] if number <= len(planned) else {}
        prefix = f"Slide {number}: "
        title = compact(entry.get("title", ""))
        if "title" in entry and (
            not title
            or title not in {compact(shape["text"]) for shape in actual["shapes"]}
        ):
            issues.append(prefix + "declared title is not an actual PPTX text shape.")
        body = entry.get("body", [])
        if not isinstance(body, list) or any(
            not isinstance(text, str) for text in body
        ):
            raise TypeError(prefix + "body must be a list of declared text paragraphs")
        if not _check_body(actual, title, body):
            issues.append(
                prefix
                + "declared body text is absent or reuses an already-counted span."
            )
        unknown_sources = set(entry.get("section_ids", [])) - section_ids
        if sections and unknown_sources:
            warnings.append(
                prefix + f"source map has unknown sections: {sorted(unknown_sources)}."
            )
        declared_topics = set(entry.get("topic_ids", []))
        covered.update(declared_topics)
        if topics and declared_topics - topic_ids:
            warnings.append(prefix + "topic map has IDs not listed in key_topics.")
        stage = entry.get("narrative_stage")
        if stage in stage_ranks:
            rank = stage_ranks[stage]
            if rank < last_stage:
                warnings.append(
                    prefix
                    + "returns to an earlier narrative stage; review the transition."
                )
            last_stage = rank
        elif stage and narrative_order:
            warnings.append(
                prefix + f"narrative stage {stage!r} is not in the outline."
            )
        units = sum(text_units(text) for text in body)
        baseline = entry.get("baseline_body_units")
        comparable = (
            isinstance(baseline, (int, float))
            and not isinstance(baseline, bool)
            and math.isfinite(baseline)
            and baseline > 0
        )
        ratio = units / baseline if comparable else None
        if comparable and not (
            plan.get("baseline_source") and entry.get("baseline_mapping")
        ):
            warnings.append(
                prefix + "density comparison lacks a documented comparable baseline."
            )
        for shape in actual["shapes"]:
            x, y, text = shape["x"], shape["y"], shape["text"]
            if (
                x is not None
                and y is not None
                and x < width * 0.5
                and y >= height * 0.82
            ):
                if FOOTER.fullmatch(text.strip()) or re.fullmatch(
                    r"\s*\d+(?:\s*/\s*\d+)?\s*", text
                ):
                    warnings.append(
                        prefix
                        + f"possible lower-left figure/page label: {text!r}; inspect before removing, since this may be a chart label."
                    )
        if entry.get("layout"):
            layouts.append(entry["layout"])
        measurements.append(
            {
                "slide": number,
                "title": entry.get("title"),
                "body_units": units,
                "declared_body_units": units,
                "extracted_text_units": text_units(actual["text"]),
                "extracted_text": actual["text"],
                "declared_figure_ids": entry.get("figure_ids", []),
                "picture_objects": actual["picture_count"],
                "visibility_verified": False,
                "baseline_body_units": baseline,
                "density_ratio": round(ratio, 4) if ratio is not None else None,
                "density_is_advisory": True,
                "topic_ids": sorted(declared_topics),
                "narrative_stage": stage,
                "layout": entry.get("layout"),
            }
        )
    missing = sorted(topic_ids - covered)
    if missing:
        warnings.append(
            f"Key topics have no declared slide mapping: {missing}. Check coverage manually."
        )
    if len(layouts) >= 3 and len(set(layouts)) == 1:
        warnings.append(
            "All recorded layouts are identical; review whether different content needs a different arrangement."
        )
    experimental = sum(bool(entry.get("experimental")) for entry in planned)
    budget = plan.get("experiment_page_budget")
    if budget is not None and experimental > int(budget):
        warnings.append(
            f"Experimental content uses {experimental} pages, above the planned {budget}; "
            "prefer readable evidence over enforcing this count."
        )
    artifact_hash = _digest(pptx_path)
    reader_review = _reader_review(plan, artifact_hash)
    if plan.get("reader_review") and not reader_review["current"]:
        warnings.append(
            "The optional reader-review notes do not refer to the current PPTX."
        )
    if reader_review["recorded"] and not reader_review["resolved"]:
        warnings.append("The reader-review record still lists unresolved issues.")
    return {
        "ok": not issues,
        "schema_version": "pptagent.paper.audit.v3",
        "scope": "Extracted PPTX structure and optional plan comparisons; XML text, picture objects, and figure IDs do not establish visibility, comprehension, or source accuracy",
        "artifact_sha256": artifact_hash,
        "plan_sha256": _digest(plan_path) if plan_path else None,
        "slides": len(slides),
        "experimental_slides": experimental,
        "measurements": measurements,
        "issues": issues,
        "warnings": warnings,
        "coverage": {
            "declared_topic_ids": sorted(covered),
            "unmapped_topic_ids": missing,
            "verified_semantically": False,
        },
        "reader_review": reader_review,
        "page_budget_reason": plan.get("page_budget_reason") or page_budget_reason,
        "manual_checks": [
            "Background, motivation, definitions, transitions, and first-time-reader understanding",
            "Source accuracy, key-topic coverage, assumptions, evidence, and limitations",
            "Useful layout variation, figure readability, template fidelity, and white background",
            "Grouped or inherited footer objects and meaningful source labels inside figures",
        ],
    }
