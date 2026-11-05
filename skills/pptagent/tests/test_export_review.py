"""Synthetic XML/image fixtures test review plumbing, not rendering or human judgment."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from pptagent_runtime import core

spec = importlib.util.spec_from_file_location(
    "export_review_cli", SCRIPTS / "pptagent.py"
)
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)
STRICT = {"delivery": {"mode": "strict"}}


class ExportReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.workspace = Path(temp.name)
        (self.workspace / "task.json").write_text(
            json.dumps(
                {
                    "profile": "paper",
                    "slides": 2,
                    "aspect_ratio": "16:9",
                    "language": "en",
                }
            )
        )
        core.scaffold(self.workspace)
        self.answer = self.workspace / "answer.pptx"
        ns = 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
        with zipfile.ZipFile(self.answer, "w") as archive:
            archive.writestr(
                "ppt/presentation.xml",
                f'<p:presentation {ns} xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldIdLst><p:sldId id="1" r:id="rId1"/><p:sldId id="2" r:id="rId2"/></p:sldIdLst><p:sldSz cx="1600" cy="900"/></p:presentation>',
            )
            archive.writestr(
                "ppt/_rels/presentation.xml.rels",
                '<Relationships><Relationship Id="rId1" Target="slides/slide1.xml"/><Relationship Id="rId2" Target="slides/slide2.xml"/></Relationships>',
            )
            for number in (1, 2):
                archive.writestr(
                    f"ppt/slides/slide{number}.xml",
                    f"<p:sld {ns}><p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>Synthetic page {number}</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>",
                )
        self.pages = [self.make_image(f"qa/deck/page-{n:02d}.jpg") for n in (1, 2)]
        self.contact = self.make_image("qa/deck/contact-01.jpg")
        self.rendered = {
            "ok": True,
            "pages": self.pages,
            "contact_sheets": [self.contact],
            "renderer": "synthetic-test",
        }
        state = core.load_state(self.workspace)
        state["renders"]["deck"] = {
            "inputs": {"artifact_sha256": core.sha256(self.answer)},
            "images": {
                name: core.sha256(self.workspace / name)
                for name in self.pages + [self.contact]
            },
            "renderer": "synthetic-test",
            "pages": self.pages,
        }
        files = core.slide_files(self.workspace)
        state["build"] = {
            "artifact_sha256": core.sha256(self.answer),
            "inputs": core.input_snapshot(self.workspace, files),
        }
        for slide in files:
            name = str(slide.relative_to(self.workspace))
            state["renders"]["slides"][name] = {
                "inputs": core.input_snapshot(self.workspace, [slide]),
                "images": {self.pages[0]: core.sha256(self.workspace / self.pages[0])},
            }
        core.save_state(self.workspace, state)
        for slide in files:
            core.record_slide_review(
                self.workspace,
                str(slide.relative_to(self.workspace)),
                "pass",
                "Synthetic test evidence",
                [],
                "synthetic-test",
            )
        core.record_deck_review(
            self.workspace, "pass", "Synthetic test evidence", [], "synthetic-test"
        )

    def make_image(self, name: str) -> str:
        path = self.workspace / name
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (160, 90), "white").save(path)
        return name

    def test_page_failure_or_uncertainty_cannot_be_masked_by_overview(self) -> None:
        for verdict in ("fail", "unjudgeable"):
            with self.subTest(verdict=verdict):
                reports = [
                    {"verdict": "pass", "summary": "First page", "issues": []},
                    {
                        "verdict": verdict,
                        "summary": "Second page unreadable",
                        "issues": [
                            {
                                "slide": 99,
                                "severity": "major",
                                "description": "Unreadable labels",
                                "suggested_fix": "Enlarge labels",
                            }
                        ],
                    },
                    {
                        "verdict": "pass",
                        "summary": "Overview looks consistent",
                        "issues": [],
                    },
                ]
                with (
                    patch.object(cli.core, "render_deck", return_value=self.rendered),
                    patch.object(cli, "review_images", side_effect=reports) as review,
                ):
                    result = cli.review_deck({"mode": "text"}, self.workspace)
                self.assertFalse(result["ok"])
                self.assertEqual(result["review"]["verdict"], verdict)
                self.assertEqual(result["review"]["issues"][0]["slide"], 2)
                self.assertEqual(
                    [call.args[1] for call in review.call_args_list],
                    [
                        [self.workspace / self.pages[0]],
                        [self.workspace / self.pages[1]],
                        [self.workspace / self.contact],
                    ],
                )
                self.assertFalse(core.finalize(self.workspace, STRICT)["complete"])

    def test_overview_failure_is_not_masked_by_page_passes(self) -> None:
        reports = [
            {"verdict": "pass", "summary": "First page", "issues": []},
            {"verdict": "pass", "summary": "Second page", "issues": []},
            {"verdict": "fail", "summary": "Narrative contradiction", "issues": []},
        ]
        with (
            patch.object(cli.core, "render_deck", return_value=self.rendered),
            patch.object(cli, "review_images", side_effect=reports),
        ):
            self.assertFalse(cli.review_deck({"mode": "text"}, self.workspace)["ok"])

    def test_all_page_and_overview_passes_accept_synthetic_evidence(self) -> None:
        report = {"verdict": "pass", "summary": "Synthetic pass", "issues": []}
        with (
            patch.object(cli.core, "render_deck", return_value=self.rendered),
            patch.object(cli, "review_images", return_value=report),
        ):
            self.assertTrue(cli.review_deck({"mode": "text"}, self.workspace)["ok"])
        self.assertTrue(core.finalize(self.workspace, STRICT)["complete"])

    def test_full_page_edit_invalidates_review_even_with_unchanged_contact(
        self,
    ) -> None:
        self.assertTrue(core.finalize(self.workspace, STRICT)["complete"])
        contact_hash = core.sha256(self.workspace / self.contact)
        Image.new("RGB", (160, 90), "black").save(self.workspace / self.pages[1])
        report = core.finalize(self.workspace, STRICT)
        self.assertEqual(core.sha256(self.workspace / self.contact), contact_hash)
        self.assertFalse(report["checks"]["deck_review_current"])
        self.assertFalse(report["complete"])

    def test_paper_finalization_needs_evidence_but_no_plan_signature(self) -> None:
        report = core.finalize(self.workspace, STRICT)
        self.assertTrue(report["complete"], report)
        self.assertIsNone(report["paper_audit"]["plan_sha256"])
        self.assertNotIn("reader_review_current", report["checks"])
        original = core.load_state(self.workspace)
        for missing in ("build", "slides", "deck"):
            with self.subTest(missing_evidence=missing):
                state = json.loads(json.dumps(original))
                if missing == "build":
                    state["build"] = {}
                else:
                    state["reviews"][missing] = {}
                core.save_state(self.workspace, state)
                self.assertFalse(core.finalize(self.workspace, STRICT)["complete"])

    def test_contact_only_legacy_review_needs_fresh_full_pages(self) -> None:
        state = core.load_state(self.workspace)
        state["reviews"]["deck"]["render"].pop("pages")
        state["renders"]["deck"].pop("pages")
        core.save_state(self.workspace, state)
        self.assertFalse(
            core.finalize(self.workspace, STRICT)["checks"]["deck_review_current"]
        )
        with self.assertRaisesRegex(ValueError, "deck render"):
            core.record_deck_review(
                self.workspace, "pass", "Synthetic test", [], "synthetic-test"
            )

    def test_incomplete_page_inventory_is_not_current(self) -> None:
        state = core.load_state(self.workspace)
        for pages in (
            [self.pages[0]],
            [self.pages[0], self.pages[0]],
            [self.pages[0], "missing.jpg"],
        ):
            with self.subTest(pages=pages):
                render = dict(state["renders"]["deck"], pages=pages)
                self.assertFalse(
                    core.deck_render_current(
                        self.workspace, render, core.sha256(self.answer), 2
                    )
                )

    def test_changed_plan_is_freshly_audited_without_invalidating_render(self) -> None:
        plan = self.workspace / "paper-plan.json"
        plan.write_text(
            json.dumps(
                {
                    "slides": [
                        {"title": "Synthetic page 1"},
                        {"title": "Synthetic page 2"},
                    ]
                }
            )
        )
        self.assertTrue(core.finalize(self.workspace, STRICT)["complete"])
        before = core.input_snapshot(self.workspace, core.slide_files(self.workspace))
        plan.write_text(
            json.dumps(
                {"slides": [{"title": "Invented title"}, {"title": "Synthetic page 2"}]}
            )
        )
        report = core.finalize(self.workspace, STRICT)
        self.assertEqual(
            before,
            core.input_snapshot(self.workspace, core.slide_files(self.workspace)),
        )
        self.assertTrue(report["checks"]["build_current"])
        self.assertTrue(report["checks"]["slide_reviews_current"])
        self.assertTrue(report["checks"]["deck_review_current"])
        self.assertFalse(report["checks"]["paper_contract"])
        self.assertFalse(report["complete"])

    def test_budget_reason_does_not_change_render_inputs(self) -> None:
        before = core.input_snapshot(self.workspace, core.slide_files(self.workspace))
        path = self.workspace / "task.json"
        task = json.loads(path.read_text())
        task["page_budget_reason"] = "More readable evidence"
        path.write_text(json.dumps(task))
        self.assertEqual(
            before,
            core.input_snapshot(self.workspace, core.slide_files(self.workspace)),
        )

    def test_mocked_renderer_tracks_pages_and_contacts_and_rejects_missing_page(
        self,
    ) -> None:
        for count in (2, 1):
            with self.subTest(rendered_pages=count):
                pymupdf = MagicMock()
                fake_page = MagicMock()
                fake_page.get_pixmap.return_value.save.side_effect = lambda path: (
                    Image.new("RGB", (160, 90), "white").save(path)
                )
                pymupdf.open.return_value.__enter__.return_value = [fake_page] * count
                with (
                    patch.dict(sys.modules, {"pymupdf": pymupdf}),
                    patch.object(core.subprocess, "run") as run,
                ):
                    if count == 1:
                        with self.assertRaisesRegex(
                            ValueError, "2 slides but rendered 1 pages"
                        ):
                            core.render_deck(self.workspace)
                        continue
                    result = core.render_deck(self.workspace)
                self.assertEqual(run.call_args.args[0][0], "libreoffice")
                self.assertEqual(result["renderer"], "LibreOffice")
                render = core.load_state(self.workspace)["renders"]["deck"]
                self.assertEqual(
                    set(render["images"]),
                    set(result["pages"] + result["contact_sheets"]),
                )
                self.assertEqual(len(result["pages"]), 2)


if __name__ == "__main__":
    unittest.main()
