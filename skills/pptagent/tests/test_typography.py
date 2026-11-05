"""Generic paper starter typography and converter structure regressions."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
from pptagent_runtime.typography import paper_font_family


class TypographyTests(unittest.TestCase):
    def test_chinese_default_has_explicit_cjk_families(self) -> None:
        stack = paper_font_family("zh-CN")
        self.assertTrue(stack.startswith('"Noto Sans CJK SC"'))
        self.assertIn('"Microsoft YaHei"', stack)
        self.assertTrue(stack.endswith("sans-serif"))

    def test_template_family_takes_precedence(self) -> None:
        stack = paper_font_family("zh-CN", "Source Han Serif SC")
        self.assertTrue(stack.startswith('"Source Han Serif SC", "Noto Sans CJK SC"'))

    def test_locale_specific_fallbacks(self) -> None:
        for language, family in [
            ("zh_Hant", "TC"),
            ("zh-TW", "TC"),
            ("ja-JP", "JP"),
            ("ko-KR", "KR"),
        ]:
            with self.subTest(language=language):
                self.assertTrue(
                    paper_font_family(language).startswith(f'"Noto Sans CJK {family}"')
                )

    def test_english_deck_still_supports_mixed_cjk_text(self) -> None:
        stack = paper_font_family("en", "Cambria")
        self.assertTrue(stack.startswith('"Cambria", "Arial"'))
        self.assertIn('"Noto Sans CJK SC"', stack)

    def test_family_is_quoted_without_ending_style_element(self) -> None:
        stack = paper_font_family(
            "zh", 'A "quoted" </style><script>alert(1)</script> family'
        )
        self.assertNotIn("</style>", stack)
        self.assertNotIn("<script>", stack)
        self.assertNotIn("</script>", stack)
        self.assertIn(r"\"quoted\"", stack)

    def test_duplicate_and_blank_families(self) -> None:
        self.assertEqual(paper_font_family("zh", " "), paper_font_family("zh"))
        self.assertEqual(paper_font_family("en", "Arial").count('"Arial"'), 1)

    def test_starter_keeps_borders_off_text_elements(self) -> None:
        source = (SKILL_ROOT / "assets/paper-slide-template.html").read_text()
        self.assertIn('class="title-rule"', source)
        self.assertIn("{{FONT_FAMILY}}", source)
        for selector in ("h1", "h2", "p", ".caption"):
            declarations = re.search(
                r"\n    " + re.escape(selector) + r"\s*\{([^}]+)\}", source
            )
            self.assertIsNotNone(declarations)
            self.assertNotIn("border", declarations.group(1))
        self.assertIn(".figure-led", source)
        self.assertIn(".synthesis", source)
        self.assertIn("Generic paper starter", source)
        active_html = re.sub(r"<!--.*?-->", "", source, flags=re.DOTALL)
        self.assertNotIn('class="figure"', active_html)
        self.assertNotIn("figure-placeholder", source)
        self.assertIn(".content { display: block; }", source)
        self.assertNotIn("cite its source", source)


if __name__ == "__main__":
    unittest.main()
