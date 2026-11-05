"""Font defaults for the generic paper starter, not a template override."""

from __future__ import annotations

import json


def paper_font_family(language: str, font_family: str | None = None) -> str:
    """Keep an explicit family first and add locale-appropriate CJK fallbacks.

    ``font_family`` is one family name, for example the supplied template's
    body font. Availability still depends on the renderer and presentation app.
    """
    locale = language.lower().replace("_", "-")
    if locale.startswith("ja"):
        fallbacks = ["Noto Sans CJK JP", "Yu Gothic", "Hiragino Sans"]
    elif locale.startswith("ko"):
        fallbacks = ["Noto Sans CJK KR", "Malgun Gothic", "Apple SD Gothic Neo"]
    elif locale.startswith("zh") and any(
        part in locale.split("-") for part in ("hant", "tw", "hk", "mo")
    ):
        fallbacks = ["Noto Sans CJK TC", "Microsoft JhengHei", "PingFang TC"]
    else:
        fallbacks = ["Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC"]
    families = [font_family.strip()] if font_family and font_family.strip() else []
    if not locale.startswith(("zh", "ja", "ko")):
        families.append("Arial")
    families.extend(fallbacks)
    # Quoting preserves family names; escaping '<' keeps inline CSS inside style.
    quoted = [
        json.dumps(name, ensure_ascii=False).replace("<", r"\3c ")
        for name in dict.fromkeys(families)
    ]
    return ", ".join([*quoted, "sans-serif"])
