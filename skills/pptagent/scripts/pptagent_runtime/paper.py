"""Deterministic paper-deck checks; visual review remains a separate gate."""
from __future__ import annotations

import hashlib
import itertools
import json
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
UNITS = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]|[A-Za-z0-9]+(?:[.'’_-][A-Za-z0-9]+)*")
LABEL = r"(?:fig(?:ure)?\.?|图|p(?:age)?\.?|页|slide)\s*\d+(?:\s*[-–,]\s*\d+)*"
FOOTER = re.compile(rf"(?:source\s*[:：]\s*|来源\s*[:：]\s*)?{LABEL}(?:\s*[·|;/,]?\s*{LABEL})*", re.IGNORECASE)


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
        relation_ns = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        names = [posixpath.normpath(posixpath.join("ppt", targets[item.attrib[relation_ns]])) for item in presentation.findall("p:sldIdLst/p:sldId", NS)]
        names = [name.lstrip("/") for name in names]
        slides = []
        for name in names:
            root = ET.fromstring(archive.read(name))
            shapes = []
            for shape in root.findall(".//p:sp", NS):
                paragraphs = ["".join(t.text or "" for t in p.findall(".//a:t", NS)) for p in shape.findall(".//a:p", NS)]
                text = "\n".join(paragraphs)
                offset = shape.find("p:spPr/a:xfrm/a:off", NS)
                shapes.append({"text": text, "x": int(offset.attrib["x"]) if offset is not None else None, "y": int(offset.attrib["y"]) if offset is not None else None})
            # Tables have visible text outside p:sp.
            full_text = "\n".join("".join(t.text or "" for t in p.findall(".//a:t", NS)) for p in root.findall(".//a:p", NS))
            table_texts = ["".join(t.text or "" for t in p.findall(".//a:t", NS)) for p in root.findall(".//p:graphicFrame//a:p", NS)]
            slides.append({"shapes": shapes, "text": full_text, "table_texts": table_texts})
    return slides, width, height


def _allowed_titles(sections: list[dict[str, Any]]) -> set[str]:
    choices = [[section.get("display_title", section["title"]), *section.get("title_variants", [])] for section in sections]
    return {compact(" / ".join(parts)) for parts in itertools.product(*choices)}


def audit(plan_path: Path, pptx_path: Path, page_budget_reason: str = "") -> dict[str, Any]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    slides, width, height = _slides(pptx_path)
    planned = plan.get("slides", [])
    sections = plan.get("sections", [])
    ids = [section["id"] for section in sections]
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError("paper sections must have nonempty, unique IDs in source order")
    section_map = {section["id"]: section for section in sections}
    ranks = {section_id: index for index, section_id in enumerate(ids)}
    issues: list[str] = []
    exceptions: list[dict[str, Any]] = []
    if not plan.get("template_used"):
        issues.append("Record the actual institutional template used.")
    revision = plan.get("revision", True)
    if revision and not plan.get("baseline_source"):
        issues.append("A revision needs baseline_source from the previous deck.")
    max_slides = int(plan.get("max_slides", 10))
    page_exception = plan.get("page_budget_reason", "") or page_budget_reason
    if max_slides > 10 or len(slides) > max_slides:
        if page_exception:
            exceptions.append({"check": "page_budget", "reason": page_exception})
        else:
            issues.append(f"Deck has {len(slides)} slides with budget {max_slides}; exceeding the ten-page target needs page_budget_reason.")
    if len(slides) != len(planned):
        issues.append(f"Plan has {len(planned)} slides; PPTX has {len(slides)}.")
    last_rank = -1
    seen: set[str] = set()
    measurements = []
    for number, (entry, actual) in enumerate(zip(planned, slides), 1):
        prefix = f"Slide {number}: "
        kind = entry.get("kind", "content")
        selected_ids = entry.get("section_ids", [])
        unknown = [key for key in selected_ids if key not in ranks]
        if unknown:
            issues.append(prefix + f"unknown paper sections {unknown}.")
        elif kind != "cover":
            selected_ranks = [ranks[key] for key in selected_ids]
            if not selected_ranks or selected_ranks != list(range(min(selected_ranks), max(selected_ranks) + 1)) or min(selected_ranks) < last_rank:
                issues.append(prefix + "sections must be consecutive and follow paper order.")
            if selected_ranks:
                last_rank = max(selected_ranks)
            if compact(entry.get("title", "")) not in _allowed_titles([section_map[key] for key in selected_ids]):
                issues.append(prefix + "title is not a recorded paper heading or faithful continuation.")
        seen.update(selected_ids)
        title = compact(entry.get("title", ""))
        if not title or title not in {compact(shape["text"]) for shape in actual["shapes"]}:
            issues.append(prefix + "declared title is not an actual PPTX text shape.")
        body = entry.get("body", [])
        if not isinstance(body, list) or any(not isinstance(text, str) for text in body):
            raise TypeError(prefix + "body must be a list of visible explanatory paragraphs")
        remaining = [compact(shape["text"]) for shape in actual["shapes"] if compact(shape["text"]) != title]
        remaining.extend(compact(text) for text in actual["table_texts"])
        for declared in sorted((compact(text) for text in body), key=len, reverse=True):
            match = next((i for i, region in enumerate(remaining) if declared and declared in region), None)
            if match is None:
                issues.append(prefix + "declared body text is absent from the PPTX or reuses an already-counted text span.")
                break
            remaining[match] = remaining[match].replace(declared, "\0", 1)
        units = sum(text_units(text) for text in body)
        baseline = entry.get("baseline_body_units")
        exception = entry.get("density_exception", "")
        exempt = bool(exception)
        if exempt:
            exceptions.append({"slide": number, "check": "body_density", "reason": exception})
        if kind == "text-only" and entry.get("figure_ids"):
            issues.append(prefix + "a text-only density exception cannot contain figures.")
        ratio = None
        if kind != "cover" and revision:
            if not isinstance(baseline, (int, float)) or isinstance(baseline, bool) or baseline <= 0:
                if not exempt:
                    issues.append(prefix + "missing positive previous-body baseline.")
            else:
                ratio = units / baseline
                if not entry.get("baseline_mapping"):
                    issues.append(prefix + "record which previous content supplies the baseline.")
                if not 1.5 <= ratio <= 2.0 and not exempt:
                    issues.append(prefix + f"body density is {ratio:.3f}x; expected 1.5–2.0x.")
        for shape in actual["shapes"]:
            x, y, text = shape["x"], shape["y"], shape["text"]
            if x is not None and y is not None and x < width * .5 and y >= height * .82:
                if FOOTER.fullmatch(text.strip()) or re.fullmatch(r"\s*\d+(?:\s*/\s*\d+)?\s*", text):
                    issues.append(prefix + f"remove lower-left figure/page label: {text!r}.")
        measurements.append({"slide": number, "title": entry.get("title"), "body_units": units, "baseline_body_units": baseline, "density_ratio": round(ratio, 4) if ratio is not None else None, "density_target_met": 1.5 <= ratio <= 2.0 if ratio is not None else None, "density_exception": exception if exempt else None})
    missing = [key for key in ids if key not in seen]
    if missing:
        issues.append(f"Paper sections missing from the slide plan: {missing}.")
    experimental = sum(bool(entry.get("experimental")) for entry in planned)
    budget = int(plan.get("experiment_page_budget", 2))
    if experimental > budget:
        if plan.get("experiment_budget_exception"):
            exceptions.append({"check": "experiment_page_budget", "reason": plan["experiment_budget_exception"]})
        else:
            issues.append(f"Experimental content uses {experimental} slides; plan budget is {budget}. Record experiment_budget_exception if readability requires more.")
    if experimental and not plan.get("experiment_layout_reason"):
        issues.append("Record the compact experiment layout and readability rationale.")
    if budget > 2 and not plan.get("experiment_layout_reason"):
        issues.append("An expanded experiment budget needs a readability or evidence reason.")
    return {"ok": not issues, "schema_version": "pptagent.paper.audit.v1", "artifact_sha256": _digest(pptx_path), "plan_sha256": _digest(plan_path), "slides": len(slides), "experimental_slides": experimental, "measurements": measurements, "issues": issues, "exceptions": exceptions, "manual_checks": ["Template fidelity; white/transparent background; academic style", "Faithful source headings and complete figure inventory", "Previous body-text selection and section regrouping", "Figure and body readability; grouped or inherited footer objects"]}
