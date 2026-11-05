"""Paper profile and actual-PPTX acceptance regressions without a browser."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from pptagent_runtime import core, paper

spec = importlib.util.spec_from_file_location("paper_cli", SCRIPTS / "pptagent.py")
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class PaperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        self.plan = {
            "template_used": "private user template",
            "baseline_source": "previous.pptx",
            "sections": [{"id": "1", "title": "1 Introduction"}],
            "slides": [
                {
                    "title": "1 Introduction",
                    "section_ids": ["1"],
                    "body": ["one two three four five six seven eight"],
                    "baseline_body_units": 5,
                    "baseline_mapping": "previous slide 2",
                }
            ],
        }
        self.pptx = self.workspace / "answer.pptx"

    def make_pptx(self, extra: str = "", title: str = "1 Introduction") -> None:
        def shape(text: str, x: int = 100, y: int = 100) -> str:
            return f'<p:sp><p:spPr><a:xfrm><a:off x="{x}" y="{y}"/></a:xfrm></p:spPr><p:txBody><a:p><a:r><a:t>{escape(text)}</a:t></a:r></a:p></p:txBody></p:sp>'

        ns = f'xmlns:p="{paper.NS["p"]}" xmlns:a="{paper.NS["a"]}"'
        body = shape(title) + shape("one two three four five six seven eight", y=300)
        if extra:
            body += shape(extra, y=930)
        with zipfile.ZipFile(self.pptx, "w") as archive:
            archive.writestr(
                "ppt/presentation.xml",
                f'<p:presentation {ns} xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldIdLst><p:sldId id="1" r:id="rId1"/></p:sldIdLst><p:sldSz cx="1600" cy="1000"/></p:presentation>',
            )
            archive.writestr(
                "ppt/_rels/presentation.xml.rels",
                '<Relationships><Relationship Id="rId1" Target="slides/slide1.xml"/></Relationships>',
            )
            archive.writestr(
                "ppt/slides/slide1.xml",
                f"<p:sld {ns}><p:cSld><p:spTree>{body}</p:spTree></p:cSld></p:sld>",
            )

    def audit(self) -> dict:
        path = self.workspace / "paper-plan.json"
        path.write_text(json.dumps(self.plan), encoding="utf-8")
        return paper.audit(path, self.pptx)

    def test_default_init_is_eight_page_paper_profile(self) -> None:
        args = cli.make_parser().parse_args(
            ["init", "--workspace", str(self.workspace)]
        )
        cli.init_workspace(args)
        task = core.load_task(self.workspace)
        self.assertEqual((task["slides"], task["profile"]), (8, "paper"))
        core.scaffold(self.workspace)
        html = (self.workspace / "slides/slide01.html").read_text()
        self.assertIn("#ffffff", html)
        self.assertIn("explanatory page title", html)
        self.assertNotIn("SLIDE 01", html)

    def test_init_template_font_reaches_scaffold(self) -> None:
        args = cli.make_parser().parse_args(
            [
                "init",
                "--workspace",
                str(self.workspace),
                "--slides",
                "1",
                "--font-family",
                "Source Han Serif SC",
            ]
        )
        cli.init_workspace(args)
        self.assertEqual(
            core.load_task(self.workspace)["font_family"], "Source Han Serif SC"
        )
        core.scaffold(self.workspace)
        source = (self.workspace / "slides/slide01.html").read_text()
        self.assertIn('font-family: "Source Han Serif SC", "Noto Sans CJK SC"', source)
        self.assertNotIn("{{FONT_FAMILY}}", source)

    def test_paper_page_count_is_a_planning_target(self) -> None:
        args = cli.make_parser().parse_args(
            ["init", "--workspace", str(self.workspace), "--slides", "11"]
        )
        self.assertTrue(cli.init_workspace(args)["ok"])

    def test_cjk_and_latin_measurement(self) -> None:
        self.assertEqual(paper.text_units("方法 MCMC 1.5 倍"), 5)

    def test_valid_density_uses_actual_pptx(self) -> None:
        self.make_pptx()
        report = self.audit()
        self.assertTrue(report["ok"], report["issues"])
        self.assertEqual(report["measurements"][0]["density_ratio"], 1.6)

    def test_absent_body_and_fake_title_fail(self) -> None:
        self.make_pptx(title="Arbitrary slogan")
        self.plan["slides"][0]["body"] = ["invented body not present"]
        report = self.audit()
        self.assertFalse(report["ok"])
        self.assertTrue(any("title" in issue for issue in report["issues"]))
        self.assertTrue(any("body text" in issue for issue in report["issues"]))

    def test_density_has_no_acceptance_threshold(self) -> None:
        self.make_pptx()
        self.plan["slides"][0]["baseline_body_units"] = 8
        report = self.audit()
        self.assertTrue(report["ok"])
        self.assertEqual(report["measurements"][0]["density_ratio"], 1.0)
        self.assertNotIn("density_target_met", report["measurements"][0])

    def test_baseline_and_density_exception_are_optional(self) -> None:
        self.make_pptx()
        entry = self.plan["slides"][0]
        entry.pop("baseline_body_units")
        entry.pop("baseline_mapping")
        self.plan.pop("baseline_source")
        entry.update(kind="text-only")
        self.assertTrue(self.audit()["ok"])

    def test_lower_left_source_label_is_advisory(self) -> None:
        for label in ("Fig. 1 · p. 4", "图 3", "p6", "2"):
            with self.subTest(label=label):
                self.make_pptx(extra=label)
                report = self.audit()
                self.assertTrue(report["ok"])
                self.assertTrue(
                    any("lower-left" in warning for warning in report["warnings"])
                )

    def test_synthesized_title_needs_no_literal_section_mapping(self) -> None:
        title = "Why simulator state is hard to validate"
        self.make_pptx(title=title)
        self.plan["slides"][0]["title"] = title
        self.assertTrue(self.audit()["ok"])

    def test_section_omission_and_experiment_budget_do_not_block(self) -> None:
        self.make_pptx()
        self.plan["sections"].append({"id": "2", "title": "2 Method"})
        self.plan["slides"][0]["experimental"] = True
        self.plan["experiment_page_budget"] = 0
        report = self.audit()
        self.assertTrue(report["ok"])
        self.assertTrue(
            any("Experimental" in warning for warning in report["warnings"])
        )

    def test_plan_change_preserves_snapshot_but_fresh_audit_catches_mismatch(
        self,
    ) -> None:
        self.test_default_init_is_eight_page_paper_profile()
        self.make_pptx()
        self.audit()
        files = core.slide_files(self.workspace)
        before = core.input_snapshot(self.workspace, files)
        self.plan["slides"][0]["title"] = "Different"
        self.audit()
        self.assertEqual(before, core.input_snapshot(self.workspace, files))
        self.assertFalse(self.audit()["ok"])

    def test_lower_body_figure_reference_is_not_a_footer(self) -> None:
        self.make_pptx(extra="Compared with Fig. 1, this method reduces the error.")
        self.assertTrue(self.audit()["ok"])

    def test_title_substring_in_body_is_not_removed(self) -> None:
        self.make_pptx()
        with zipfile.ZipFile(self.pptx) as archive:
            members = {name: archive.read(name) for name in archive.namelist()}
        old_body = b"one two three four five six seven eight"
        new_body = b"1 Introduction explains one two three four five"
        root = ET.fromstring(
            members["ppt/slides/slide1.xml"].replace(old_body, new_body)
        )
        shapes = root.find("p:cSld/p:spTree", paper.NS)
        shapes[:] = list(reversed(list(shapes)))
        members["ppt/slides/slide1.xml"] = ET.tostring(root)
        with zipfile.ZipFile(self.pptx, "w") as archive:
            for name, content in members.items():
                archive.writestr(name, content)
        self.plan["slides"][0]["body"] = [new_body.decode()]
        self.assertTrue(self.audit()["ok"])

    def test_repeated_body_cannot_inflate_actual_density(self) -> None:
        self.make_pptx()
        self.plan["slides"][0]["body"] *= 2
        self.plan["slides"][0]["baseline_body_units"] = 8
        self.assertFalse(self.audit()["ok"])

    def test_key_topic_coverage_is_declared_not_inferred(self) -> None:
        self.make_pptx()
        self.plan["key_topics"] = [{"id": "background", "label": "Problem setting"}]
        report = self.audit()
        self.assertTrue(report["ok"])
        self.assertEqual(report["coverage"]["unmapped_topic_ids"], ["background"])
        self.assertFalse(report["coverage"]["verified_semantically"])
        self.plan["slides"][0]["topic_ids"] = ["background"]
        self.assertEqual(self.audit()["coverage"]["unmapped_topic_ids"], [])

    def test_continuation_title_is_allowed(self) -> None:
        title = "1 Introduction (continued)"
        self.make_pptx(title=title)
        self.plan["sections"][0]["title_variants"] = [title]
        self.plan["slides"][0]["title"] = title
        self.assertTrue(self.audit()["ok"])

    def test_later_source_figure_can_appear_early(self) -> None:
        self.make_pptx()
        self.plan["sections"] += [
            {"id": "2", "title": "Background"},
            {"id": "3", "title": "Motivation"},
        ]
        self.plan["slides"][0].update(section_ids=["1", "3"], figure_ids=["fig1"])
        self.assertTrue(self.audit()["ok"])

    def test_page_budget_reason_is_preserved_without_hard_gate(self) -> None:
        args = cli.make_parser().parse_args(
            [
                "init",
                "--workspace",
                str(self.workspace),
                "--slides",
                "11",
                "--page-budget-reason",
                "Readable evidence",
            ]
        )
        self.assertTrue(cli.init_workspace(args)["ok"])
        self.assertEqual(
            core.load_task(self.workspace)["page_budget_reason"], "Readable evidence"
        )
        self.make_pptx()
        self.plan["max_slides"] = 0
        report = self.audit()
        self.assertTrue(report["ok"])
        self.assertTrue(
            any("planning target" in warning for warning in report["warnings"])
        )

    def test_actual_presentation_order_not_file_number(self) -> None:
        self.make_pptx()
        with zipfile.ZipFile(self.pptx) as archive:
            members = {name: archive.read(name) for name in archive.namelist()}
        members["ppt/slides/slide2.xml"] = members["ppt/slides/slide1.xml"].replace(
            b"1 Introduction", b"2 Method"
        )
        members["ppt/presentation.xml"] = members["ppt/presentation.xml"].replace(
            b'<p:sldId id="1" r:id="rId1"/>',
            b'<p:sldId id="2" r:id="rId2"/><p:sldId id="1" r:id="rId1"/>',
        )
        members["ppt/_rels/presentation.xml.rels"] = members[
            "ppt/_rels/presentation.xml.rels"
        ].replace(
            b"</Relationships>",
            b'<Relationship Id="rId2" Target="slides/slide2.xml"/></Relationships>',
        )
        with zipfile.ZipFile(self.pptx, "w") as archive:
            for name, content in members.items():
                archive.writestr(name, content)
        slides, _, _ = paper._slides(self.pptx)
        self.assertIn("2 Method", slides[0]["text"])

    def record_reader_review(self) -> None:
        self.plan["reader_review"] = {
            "artifact_sha256": core.sha256(self.pptx),
            "reviewer": "First-time-reader review",
            "findings": [
                {
                    "slide": 1,
                    "problem": "Undefined term",
                    "change": "Added a definition",
                }
            ],
            "coverage_notes": "Checked the problem, mechanism, evidence, and limitations.",
            "remaining_issues": [],
        }

    def test_reader_review_is_artifact_bound_not_automatic_comprehension(self) -> None:
        self.make_pptx()
        report = self.audit()
        self.assertFalse(report["reader_review"]["current"])
        self.record_reader_review()
        review = self.audit()["reader_review"]
        self.assertTrue(review["current"])
        self.assertTrue(review["resolved"])
        self.assertFalse(review["comprehension_verified_automatically"])
        self.plan["reader_review"]["artifact_sha256"] = "outdated"
        self.assertFalse(self.audit()["reader_review"]["current"])

    def test_empty_or_malformed_reader_evidence_does_not_pass(self) -> None:
        self.make_pptx()
        for overrides in (
            {"reviewer": "   "},
            {"coverage_notes": "\n"},
            {"reviewer": True, "coverage_notes": 42},
            {"findings": [None]},
            {"findings": [{"problem": "Undefined term", "change": "  "}]},
        ):
            with self.subTest(overrides=overrides):
                self.record_reader_review()
                self.plan["reader_review"].update(overrides)
                self.assertFalse(self.audit()["reader_review"]["current"])
        self.record_reader_review()
        self.plan["reader_review"]["findings"] = []
        self.assertTrue(self.audit()["reader_review"]["current"])

    def test_reader_review_update_does_not_trigger_a_circular_rebuild(self) -> None:
        self.test_default_init_is_eight_page_paper_profile()
        self.make_pptx()
        self.audit()
        files = core.slide_files(self.workspace)
        before = core.input_snapshot(self.workspace, files)
        self.record_reader_review()
        self.audit()
        self.assertEqual(before, core.input_snapshot(self.workspace, files))
        self.plan["slides"][0]["title"] = "Changed content"
        self.audit()
        self.assertEqual(before, core.input_snapshot(self.workspace, files))
        self.assertFalse(self.audit()["ok"])

    def test_optional_reader_notes_are_reported_without_separate_final_gate(
        self,
    ) -> None:
        self.make_pptx()
        (self.workspace / "task.json").write_text(
            json.dumps(
                {
                    "profile": "paper",
                    "slides": 1,
                    "aspect_ratio": "16:9",
                    "language": "en",
                }
            )
        )
        self.record_reader_review()
        self.plan["reader_review"]["remaining_issues"] = ["Motivation unclear"]
        self.audit()
        report = core.finalize(self.workspace, {"delivery": {"mode": "strict"}})
        self.assertNotIn("reader_review_current", report["checks"])
        self.assertNotIn("reader_review_resolved", report["checks"])
        self.assertFalse(report["paper_audit"]["reader_review"]["resolved"])
        self.assertFalse(report["complete"])

    def test_section_metadata_is_optional(self) -> None:
        self.make_pptx()
        self.plan.pop("sections")
        self.plan["slides"][0].pop("section_ids")
        self.assertTrue(self.audit()["ok"])

    def duplicate_slides(self, count: int) -> None:
        with zipfile.ZipFile(self.pptx) as archive:
            members = {name: archive.read(name) for name in archive.namelist()}
        slide_ids = "".join(
            f'<p:sldId id="{i}" r:id="rId{i}"/>' for i in range(1, count + 1)
        )
        relationships = "".join(
            f'<Relationship Id="rId{i}" Target="slides/slide{i}.xml"/>'
            for i in range(1, count + 1)
        )
        members["ppt/presentation.xml"] = members["ppt/presentation.xml"].replace(
            b'<p:sldId id="1" r:id="rId1"/>', slide_ids.encode()
        )
        members["ppt/_rels/presentation.xml.rels"] = (
            f"<Relationships>{relationships}</Relationships>".encode()
        )
        for number in range(2, count + 1):
            members[f"ppt/slides/slide{number}.xml"] = members["ppt/slides/slide1.xml"]
        with zipfile.ZipFile(self.pptx, "w") as archive:
            for name, content in members.items():
                archive.writestr(name, content)
        self.plan["slides"] = [dict(self.plan["slides"][0]) for _ in range(count)]

    def test_repeated_layout_prompts_review_without_enforcing_columns(self) -> None:
        self.make_pptx()
        self.duplicate_slides(3)
        for entry in self.plan["slides"]:
            entry["layout"] = "two columns"
        report = self.audit()
        self.assertTrue(report["ok"])
        self.assertTrue(
            any("layouts are identical" in warning for warning in report["warnings"])
        )

    def test_narrative_return_is_advisory_not_subsection_order_gate(self) -> None:
        self.make_pptx()
        self.duplicate_slides(2)
        self.plan["narrative_order"] = ["background", "method"]
        self.plan["slides"][0]["narrative_stage"] = "method"
        self.plan["slides"][1]["narrative_stage"] = "background"
        report = self.audit()
        self.assertTrue(report["ok"])
        self.assertTrue(
            any("earlier narrative stage" in warning for warning in report["warnings"])
        )

    def test_short_plan_does_not_hide_actual_pages(self) -> None:
        self.make_pptx(extra="undeclared words")
        self.duplicate_slides(3)
        self.plan["slides"] = self.plan["slides"][:1]
        report = self.audit()
        self.assertFalse(report["ok"])
        self.assertEqual(len(report["measurements"]), 3)
        last = report["measurements"][-1]
        self.assertEqual(last["declared_body_units"], 0)
        self.assertGreater(last["extracted_text_units"], 0)
        self.assertIn("undeclared words", last["extracted_text"])
        self.assertFalse(last["visibility_verified"])

    def test_without_plan_extracts_text_without_claiming_visibility(self) -> None:
        self.make_pptx(extra="unmapped hidden text")
        report = paper.audit(None, self.pptx)
        self.assertTrue(report["ok"])
        self.assertIsNone(report["plan_sha256"])
        self.assertGreater(report["measurements"][0]["extracted_text_units"], 8)
        self.assertFalse(report["measurements"][0]["visibility_verified"])

    def test_table_and_off_canvas_text_are_extracted_not_certified_visible(
        self,
    ) -> None:
        self.make_pptx()
        with zipfile.ZipFile(self.pptx) as archive:
            members = {name: archive.read(name) for name in archive.namelist()}
        extra = b'<p:graphicFrame><a:tbl><a:tr><a:tc><a:txBody><a:p><a:r><a:t>table evidence</a:t></a:r></a:p></a:txBody></a:tc></a:tr></a:tbl></p:graphicFrame><p:sp><p:spPr><a:xfrm><a:off x="-99999" y="-99999"/></a:xfrm></p:spPr><p:txBody><a:p><a:r><a:t>off canvas evidence</a:t></a:r></a:p></p:txBody></p:sp>'
        members["ppt/slides/slide1.xml"] = members["ppt/slides/slide1.xml"].replace(
            b"</p:spTree>", extra + b"</p:spTree>"
        )
        with zipfile.ZipFile(self.pptx, "w") as archive:
            for name, content in members.items():
                archive.writestr(name, content)
        measurement = paper.audit(None, self.pptx)["measurements"][0]
        self.assertIn("table evidence", measurement["extracted_text"])
        self.assertIn("off canvas evidence", measurement["extracted_text"])
        self.assertEqual(measurement["extracted_text_units"], 15)
        self.assertFalse(measurement["visibility_verified"])

    def test_declared_figure_ids_are_not_verified_picture_objects(self) -> None:
        self.make_pptx()
        self.plan["slides"][0]["figure_ids"] = ["invented-figure"]
        measurement = self.audit()["measurements"][0]
        self.assertEqual(measurement["declared_figure_ids"], ["invented-figure"])
        self.assertEqual(measurement["picture_objects"], 0)
        self.assertFalse(measurement["visibility_verified"])


if __name__ == "__main__":
    unittest.main()
