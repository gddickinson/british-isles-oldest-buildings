"""Themes: neon (the default), light and dark. Token completeness, neon as the default everywhere, contrast.

The neon tokens live in style.css (:root[data-theme="neon"]); its flourishes in neon.css, all scoped to neon.
"""
import re
import unittest
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"
TEMPLATES = STATIC.parent / "templates"
HEX = re.compile(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})\b")


def blocks(css):
    """(selector, body) of every rule, nested @media rules flattened."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out = []
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        out.append((m.group(1).strip(), m.group(2)))
    return out


def props(body):
    return set(re.findall(r"(--[\w-]+)\s*:", body))


def defined_for(theme):
    """Custom properties set by any rule whose selector names :root[data-theme="<theme>"] alone (not a descendant)."""
    names = set()
    for f in STATIC.glob("*.css"):
        for sel, body in blocks(f.read_text()):
            parts = [p.strip() for p in sel.split(",")]
            if any(p == f':root[data-theme="{theme}"]' for p in parts):
                names |= props(body)
    return names


def luminance(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    hi, lo = sorted([luminance(a), luminance(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


class ThemeTokens(unittest.TestCase):
    def setUp(self):
        self.style = (STATIC / "style.css").read_text()
        self.light = {sel: body for sel, body in blocks(self.style)}[":root"]
        self.neon = dict(HEX.findall({sel: body for sel, body in blocks(self.style)}[':root[data-theme="neon"]']))

    def test_neon_covers_every_style_token(self):
        neon_body = {sel: body for sel, body in blocks(self.style)}[':root[data-theme="neon"]']
        self.assertEqual(props(self.light) - props(neon_body), set())
        for k in [f"g{i}" for i in range(1, 24)] + [f"p{i}" for i in range(1, 14)] + ["bg", "panel", "ink", "muted", "line", "accent"]:
            self.assertIn(k, self.neon)

    def test_neon_covers_every_dark_variable_in_every_stylesheet(self):
        self.assertEqual(defined_for("dark") - defined_for("neon"), set())

    def test_dark_only_rules_also_apply_to_neon(self):
        # a rule written for the dark theme (other than the token blocks) has a neon twin in the same selector list
        for f in STATIC.glob("*.css"):
            for sel, _ in blocks(f.read_text()):
                token_block = f.name == "style.css" and sel == ':root[data-theme="dark"]'   # neon has its own
                if '[data-theme="dark"]' in sel and ":not(" not in sel and not token_block:
                    self.assertIn('[data-theme="neon"]', sel, f"{f.name}: {sel}")

    def test_text_contrast_wcag_aa(self):
        n = self.neon
        for fg in ("ink", "muted", "accent"):
            for bg in ("bg", "panel", "surface", "band-alt", "accent-soft"):
                self.assertGreaterEqual(contrast(n[fg], n[bg]), 4.5, f"{fg} on {bg}")
        self.assertGreaterEqual(contrast(n["bg"], n["accent"]), 4.5)          # text on accent buttons
        self.assertGreaterEqual(contrast(n["panel"], n["accent"]), 4.5)

    def test_palette_readable_on_dark_panels(self):
        n = self.neon
        for k in [f"g{i}" for i in range(1, 24)] + ["g-other"] + [f"p{i}" for i in range(1, 14)]:
            self.assertGreaterEqual(contrast(n[k], n["panel"]), 3, k)        # WCAG 1.4.11 graphics
        self.assertEqual(len({n[f"g{i}"].lower() for i in range(1, 24)}), 23)
        ramp = [luminance(n[f"p{i}"]) for i in range(1, 14)]
        self.assertEqual(ramp, sorted(ramp, reverse=True))                   # oldest lightest, in order

    def test_neon_css_only_under_neon(self):
        for sel, _ in blocks((STATIC / "neon.css").read_text()):
            if sel.startswith("@"):
                continue
            for part in sel.split(","):
                self.assertTrue(part.strip().startswith(':root[data-theme="neon"]'), part)


class NeonDefault(unittest.TestCase):
    def test_prefs_default_is_neon(self):
        js = (STATIC / "ui_prefs.js").read_text()
        self.assertRegex(js, r'theme:\s*"neon"')
        self.assertIn('THEMES = ["neon", "light", "dark"]', js)

    def test_base_template_paints_neon_before_scripts(self):
        html = (TEMPLATES / "base.html").read_text()
        self.assertIn('p.theme || "neon"', html)
        self.assertIn("neon.css", html)
        self.assertLess(html.index("neon.css"), html.index("<body"))

    def test_settings_offers_every_theme(self):
        html = (TEMPLATES / "settings.html").read_text()
        for v in ("neon", "light", "dark", "system"):
            self.assertIn(f'<option value="{v}"', html)

    def test_basemap_dark_under_neon(self):
        self.assertIn("Prefs.isDark()", (STATIC / "basemap.js").read_text())


if __name__ == "__main__":
    unittest.main()
