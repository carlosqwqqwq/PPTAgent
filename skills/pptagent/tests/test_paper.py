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
            "slides": [{"title": "1 Introduction", "section_ids": ["1"], "body": ["one two three four five six seven eight"], "baseline_body_units": 5, "baseline_mapping": "previous slide 2"}],
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
            archive.writestr("ppt/presentation.xml", f'<p:presentation {ns} xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldIdLst><p:sldId id="1" r:id="rId1"/></p:sldIdLst><p:sldSz cx="1600" cy="1000"/></p:presentation>')
            archive.writestr("ppt/_rels/presentation.xml.rels", '<Relationships><Relationship Id="rId1" Target="slides/slide1.xml"/></Relationships>')
            archive.writestr("ppt/slides/slide1.xml", f'<p:sld {ns}><p:cSld><p:spTree>{body}</p:spTree></p:cSld></p:sld>')

    def audit(self) -> dict:
        path = self.workspace / "paper-plan.json"
        path.write_text(json.dumps(self.plan), encoding="utf-8")
        return paper.audit(path, self.pptx)

    def test_default_init_is_eight_page_paper_profile(self) -> None:
        args = cli.make_parser().parse_args(["init", "--workspace", str(self.workspace)])
        cli.init_workspace(args)
        task = core.load_task(self.workspace)
        self.assertEqual((task["slides"], task["profile"]), (8, "paper"))
        core.scaffold(self.workspace)
        html = (self.workspace / "slides/slide01.html").read_text()
        self.assertIn("#ffffff", html)
        self.assertIn("numbered paper section", html)
        self.assertNotIn("SLIDE 01", html)

    def test_paper_page_budget_rejects_eleven(self) -> None:
        args = cli.make_parser().parse_args(["init", "--workspace", str(self.workspace), "--slides", "11"])
        with self.assertRaisesRegex(ValueError, "ten-slide"):
            cli.init_workspace(args)

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

    def test_sparse_body_fails(self) -> None:
        self.make_pptx()
        self.plan["slides"][0]["baseline_body_units"] = 8
        self.assertFalse(self.audit()["ok"])

    def test_text_only_exception_is_explicit(self) -> None:
        self.make_pptx()
        entry = self.plan["slides"][0]
        entry.update(kind="text-only", baseline_body_units=8, density_exception="Short source section without a figure")
        self.assertTrue(self.audit()["ok"])
        entry["figure_ids"] = ["fig1"]
        self.assertFalse(self.audit()["ok"])

    def test_lower_left_source_label_fails(self) -> None:
        for label in ("Fig. 1 · p. 4", "图 3", "p6", "2"):
            with self.subTest(label=label):
                self.make_pptx(extra=label)
                self.assertTrue(any("lower-left" in issue for issue in self.audit()["issues"]))

    def test_unrelated_title_fails(self) -> None:
        self.make_pptx(title="A new perspective")
        self.plan["slides"][0]["title"] = "A new perspective"
        self.assertTrue(any("recorded paper heading" in issue for issue in self.audit()["issues"]))

    def test_missing_section_and_experiment_budget_fail(self) -> None:
        self.make_pptx()
        self.plan["sections"].append({"id": "2", "title": "2 Method"})
        self.plan["slides"][0]["experimental"] = True
        self.plan["experiment_page_budget"] = 0
        report = self.audit()
        self.assertTrue(any("missing" in issue for issue in report["issues"]))
        self.assertTrue(any("Experimental" in issue for issue in report["issues"]))

    def test_plan_change_invalidates_input_snapshot(self) -> None:
        self.test_default_init_is_eight_page_paper_profile()
        self.make_pptx()
        self.audit()
        files = core.slide_files(self.workspace)
        before = core.input_snapshot(self.workspace, files)
        self.plan["slides"][0]["title"] = "Different"
        self.audit()
        self.assertNotEqual(before, core.input_snapshot(self.workspace, files))


    def test_lower_body_figure_reference_is_not_a_footer(self) -> None:
        self.make_pptx(extra="Compared with Fig. 1, this method reduces the error.")
        self.assertTrue(self.audit()["ok"])

    def test_title_substring_in_body_is_not_removed(self) -> None:
        self.make_pptx()
        with zipfile.ZipFile(self.pptx) as archive:
            members = {name: archive.read(name) for name in archive.namelist()}
        old_body = b"one two three four five six seven eight"
        new_body = b"1 Introduction explains one two three four five"
        root = ET.fromstring(members["ppt/slides/slide1.xml"].replace(old_body, new_body))
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

    def test_content_exception_preserves_unmet_measurement(self) -> None:
        self.make_pptx()
        self.plan["slides"][0].update(baseline_body_units=8, density_exception="Regrouped source material cannot be expanded without repetition.")
        report = self.audit()
        self.assertTrue(report["ok"])
        self.assertFalse(report["measurements"][0]["density_target_met"])
        self.assertEqual(report["measurements"][0]["density_ratio"], 1.0)
        self.assertTrue(report["exceptions"])

    def test_continuation_title_is_allowed(self) -> None:
        title = "1 Introduction (continued)"
        self.make_pptx(title=title)
        self.plan["sections"][0]["title_variants"] = [title]
        self.plan["slides"][0]["title"] = title
        self.assertTrue(self.audit()["ok"])

    def test_experiment_exception_is_visible(self) -> None:
        self.make_pptx()
        self.plan["slides"][0]["experimental"] = True
        self.plan.update(experiment_page_budget=0, experiment_layout_reason="Readable panels", experiment_budget_exception="Retain necessary axes and legends at full size.")
        report = self.audit()
        self.assertTrue(report["ok"])
        self.assertEqual(report["exceptions"][0]["check"], "experiment_page_budget")

    def test_page_budget_exception_is_allowed(self) -> None:
        args = cli.make_parser().parse_args(["init", "--workspace", str(self.workspace), "--slides", "11", "--page-budget-reason", "Necessary source evidence remains readable."])
        self.assertTrue(cli.init_workspace(args)["ok"])
        task = core.load_task(self.workspace)
        self.assertEqual(task["page_budget_reason"], "Necessary source evidence remains readable.")
        self.make_pptx()
        self.plan["max_slides"] = 0
        self.audit()
        report = paper.audit(self.workspace / "paper-plan.json", self.pptx, task["page_budget_reason"])
        self.assertTrue(report["ok"], report["issues"])
        self.assertEqual(report["exceptions"][0]["check"], "page_budget")

    def test_actual_presentation_order_not_file_number(self) -> None:
        self.make_pptx()
        with zipfile.ZipFile(self.pptx) as archive:
            members = {name: archive.read(name) for name in archive.namelist()}
        members["ppt/slides/slide2.xml"] = members["ppt/slides/slide1.xml"].replace(b"1 Introduction", b"2 Method")
        members["ppt/presentation.xml"] = members["ppt/presentation.xml"].replace(b'<p:sldId id="1" r:id="rId1"/>', b'<p:sldId id="2" r:id="rId2"/><p:sldId id="1" r:id="rId1"/>')
        members["ppt/_rels/presentation.xml.rels"] = members["ppt/_rels/presentation.xml.rels"].replace(b'</Relationships>', b'<Relationship Id="rId2" Target="slides/slide2.xml"/></Relationships>')
        with zipfile.ZipFile(self.pptx, "w") as archive:
            for name, content in members.items():
                archive.writestr(name, content)
        slides, _, _ = paper._slides(self.pptx)
        self.assertIn("2 Method", slides[0]["text"])


if __name__ == "__main__":
    unittest.main()
