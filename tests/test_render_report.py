"""Renderer regression tests. Run: python3 -m unittest discover -s tests -v"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_report.py"
spec = importlib.util.spec_from_file_location("render_report", SCRIPT)
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


def read_state(html):
    return json.loads(re.search(
        r'<script id="reportState" type="application/json">(.*?)</script>',
        html, re.S,
    ).group(1))


class RenderReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.input = self.folder / "report.json"
        self.output = self.folder / "report.html"
        self.data = {
            "version": 1, "date": "2026-10-13", "title": "A clear report",
            "lead": "Start with the conclusion.",
            "sections": [{"title": "Evidence", "paragraphs": ["One point."]}],
        }
        self.locales = renderer.load_locales(ROOT)

    def render(self, data=None, flags=(), script=SCRIPT):
        self.input.write_text(json.dumps(
            data if data is not None else self.data, ensure_ascii=False,
        ), encoding="utf-8")
        result = subprocess.run([
            sys.executable, str(script), "--input", str(self.input),
            "--output", str(self.output), *flags,
        ], capture_output=True, text=True, cwd=self.folder)
        return result

    def html(self):
        return self.output.read_text(encoding="utf-8")

    def test_english_default_and_portable_catalog(self):
        self.assertEqual(self.render().returncode, 0)
        state = read_state(self.html())
        self.assertEqual(state["data"]["language"], "en")
        self.assertEqual(state["data"]["publication"], "Research report")
        self.assertIn("Appearance &amp; save", self.html())
        self.assertIn('id="reportLocales"', self.html())
        self.assertNotRegex(self.html(), r"__[A-Z0-9_]+__")
        self.assertEqual(set(state), {"data", "appearance", "revision", "updatedAt"})

    def test_all_ui_languages(self):
        for language, ui in self.locales.items():
            with self.subTest(language=language):
                self.assertEqual(self.render(
                    {**self.data, "language": language}, ("--force",),
                ).returncode, 0)
                html = self.html()
                self.assertIn(f'data-ui-language="{language}"', html)
                self.assertIn(ui["saveHtml"], html)
                self.assertEqual(
                    read_state(html)["data"]["publication"], ui["publication"],
                )

    def test_alias_matching(self):
        cases = {
            "en-GB": "en", "JA_jp": "ja", "zh": "zh-CN",
            "zh-SG": "zh-CN", "zh-Hans-CN": "zh-CN",
            "ZH_hant_TW": "zh-TW", "zh-HK": "zh-TW", "zh-MO": "zh-TW",
            "fr-FR": "en", "not a tag": "en", "zhCN": "en",
        }
        for tag, expected in cases.items():
            with self.subTest(tag=tag):
                self.assertEqual(
                    renderer.resolve_ui_language(tag, self.locales), expected,
                )
                self.assertEqual(self.render(
                    {**self.data, "language": tag}, ("--force",),
                ).returncode, 0)
                self.assertIn(f'data-ui-language="{expected}"', self.html())
                self.assertEqual(read_state(self.html())["data"]["language"], tag)

    def test_blank_language_defaults_to_english(self):
        for tag in ("", "   "):
            self.assertEqual(self.render(
                {**self.data, "language": tag}, ("--force",),
            ).returncode, 0)
            self.assertEqual(read_state(self.html())["data"]["language"], "en")

    def test_override_localizes_without_translating_prose(self):
        data = {**self.data, "language": "zh-CN", "title": "Original text"}
        self.assertEqual(self.render(data).returncode, 0)
        original = read_state(self.html())
        self.assertEqual(self.render(
            data, ("--language", "ja", "--force"),
        ).returncode, 0)
        updated = read_state(self.html())
        self.assertEqual(updated["data"]["title"], data["title"])
        self.assertEqual(updated["data"]["language"], "ja")
        self.assertNotEqual(updated["revision"], original["revision"])

    def test_explicit_legacy_locale_keeps_digest(self):
        data = {**self.data, "language": "zh-CN"}
        digest = hashlib.sha256(json.dumps(
            data, ensure_ascii=False, sort_keys=True,
        ).encode()).hexdigest()
        self.assertEqual(self.render(data).returncode, 0)
        state = read_state(self.html())
        self.assertEqual(state["revision"], digest)
        self.assertEqual(state["data"]["id"], "report-" + digest[:16])
        self.assertIn("editorial-report:v1:", self.html())

    def test_escaping_and_literal_markers(self):
        value = '</script><b>&" __REPORT_STATE_JSON__ __UI_SAVE_HTML__\u2028\u2029'
        data = {**self.data, "title": value, "language": 'en"><script>alert(1)</script>'}
        self.assertEqual(self.render(data).returncode, 0)
        self.assertEqual(read_state(self.html())["data"]["title"], value)
        self.assertNotIn("</script><b>", self.html())
        self.assertNotIn('lang="en"><script>', self.html())
        self.assertIn("__UI_SAVE_HTML__", read_state(self.html())["data"]["title"])

    def test_refuses_overwrite_unless_forced(self):
        self.assertEqual(self.render().returncode, 0)
        old = self.output.read_bytes()
        self.assertNotEqual(self.render(
            {**self.data, "title": "Changed"},
        ).returncode, 0)
        self.assertEqual(self.output.read_bytes(), old)
        self.assertEqual(self.render(
            {**self.data, "title": "Changed"}, ("--force",),
        ).returncode, 0)
        self.assertEqual(read_state(self.html())["data"]["title"], "Changed")

    def test_never_modifies_input(self):
        self.assertEqual(self.render().returncode, 0)
        self.assertEqual(json.loads(self.input.read_text()), self.data)
        before = self.input.read_bytes()
        result = subprocess.run([
            sys.executable, str(SCRIPT), "--input", str(self.input),
            "--output", str(self.input), "--force",
        ], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.input.read_bytes(), before)

    def test_invalid_data_leaves_no_output(self):
        cases = [
            {**self.data, "version": True}, {**self.data, "date": "2026-02-30"},
            {**self.data, "title": ""}, {**self.data, "sections": []},
            {**self.data, "language": 123}, {**self.data, "unexpected": True},
        ]
        for data in cases:
            with self.subTest(data=data):
                self.assertNotEqual(self.render(data).returncode, 0)
                self.assertFalse(self.output.exists())

    def test_invalid_language_flag(self):
        self.assertNotEqual(self.render(flags=("--language", "fr")).returncode, 0)
        self.assertFalse(self.output.exists())

    def test_catalog_validation(self):
        for mutate in (
            lambda c: c.pop("ja"),
            lambda c: c["en"].pop("saveHtml"),
            lambda c: c["ja"].update(aliases=[]),
            lambda c: c["zh-TW"]["themes"].pop("night"),
            lambda c: c["zh-CN"].update(unknown="text"),
        ):
            catalog = copy.deepcopy(self.locales)
            mutate(catalog)
            directory = self.folder / "isolated"
            (directory / "assets").mkdir(parents=True, exist_ok=True)
            (directory / "assets" / "locales.json").write_text(
                json.dumps(catalog), encoding="utf-8",
            )
            with self.assertRaises(renderer.InvalidReport):
                renderer.load_locales(directory)

    def test_missing_catalog_fails_clearly(self):
        script = self.folder / "isolated" / "scripts" / SCRIPT.name
        script.parent.mkdir(parents=True)
        shutil.copy2(SCRIPT, script)
        result = self.render(script=script)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("locales.json", result.stderr)
        self.assertFalse(self.output.exists())

    def test_examples_are_reproducible(self):
        for source in sorted((ROOT / "examples").rglob("*.json")):
            with self.subTest(example=source.name):
                comparison = source.stem.startswith("report-comparison")
                flags = ("--force", "--theme", "sage", "--font", "modern") if comparison else ("--force",)
                self.assertEqual(self.render(
                    json.loads(source.read_text(encoding="utf-8")), flags,
                ).returncode, 0)
                self.assertEqual(self.html(), source.with_suffix(".html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
