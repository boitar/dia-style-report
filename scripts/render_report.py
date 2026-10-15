#!/usr/bin/env python3
"""Validate plain-text report data and render a portable, editable HTML file."""
import argparse
import datetime as dt
import hashlib
from html import escape
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit

UI_LANGUAGES = ("en", "zh-CN", "ja", "zh-TW")
UI_TEXT_KEYS = {
    "publication", "reportTitle", "skipReport", "noScript", "settingsTitle",
    "closeSettings", "themeLabel", "fontLabel", "editingLabel", "saveHtml",
    "undoEdit", "initialStatus", "readingTip", "editDescription",
    "editDescriptionSingleLine", "savedStatus", "storageUnavailableStatus",
    "draftUnavailableStatus", "exportedStatus", "restoredStatus", "undoStatus",
    "chartBaseline", "chartScrollHint", "chartPointHint",
}


class InvalidReport(ValueError):
    pass


def fail(path, message):
    raise InvalidReport(f"{path}: {message}")


def obj(value, path, allowed):
    if not isinstance(value, dict):
        fail(path, "expected an object")
    unknown = set(value) - set(allowed)
    if unknown:
        fail(path, "unknown fields: " + ", ".join(sorted(unknown)))
    return value


def text(value, path, required=True):
    if not isinstance(value, str) or (required and not value.strip()):
        fail(path, "expected a nonempty string" if required else "expected a string")
    return value


def texts(value, path):
    if not isinstance(value, list):
        fail(path, "expected an array of strings")
    for i, entry in enumerate(value):
        text(entry, f"{path}[{i}]")


def optional_texts(value, path, keys):
    for key in keys:
        if key in value:
            texts(value[key], f"{path}.{key}")


def number(value, path):
    try:
        valid = type(value) in (int, float) and math.isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    if not valid:
        fail(path, "expected a finite nonnegative number")
    return value


def chart(value, path):
    obj(value, path, {"type", "title", "description", "caption", "valueLabel", "points", "axis"})
    if value.get("type") not in ("horizontal-bar", "vertical-bar"):
        fail(f"{path}.type", "expected horizontal-bar or vertical-bar")
    for key in ("title", "description", "caption", "valueLabel"):
        text(value.get(key), f"{path}.{key}")
    points = value.get("points")
    if not isinstance(points, list) or not points:
        fail(f"{path}.points", "at least one data point is required")
    for i, point in enumerate(points):
        p = f"{path}.points[{i}]"
        obj(point, p, {"label", "value", "tone", "details"})
        text(point.get("label"), f"{p}.label")
        number(point.get("value"), f"{p}.value")
        if point.get("tone", "primary") not in ("primary", "muted"):
            fail(f"{p}.tone", "expected primary or muted")
        details = point.get("details", [])
        if not isinstance(details, list):
            fail(f"{p}.details", "expected an array of text label/value pairs")
        for j, detail in enumerate(details):
            q = f"{p}.details[{j}]"
            obj(detail, q, {"label", "value"})
            for key in ("label", "value"):
                text(detail.get(key), f"{q}.{key}")
    if "axis" in value:
        axis = obj(value["axis"], f"{path}.axis", {"min", "max", "step"})
        low = number(axis.get("min"), f"{path}.axis.min")
        high = number(axis.get("max"), f"{path}.axis.max")
        if high <= low:
            fail(f"{path}.axis", "max must be greater than min")
        if "step" in axis:
            step = number(axis["step"], f"{path}.axis.step")
            if not step or (high - low) / step > 100 + 1e-8:
                fail(f"{path}.axis.step", "must be positive and produce no more than 100 intervals")
        for i, point in enumerate(points):
            if not low <= point["value"] <= high:
                fail(f"{path}.points[{i}].value", "outside the explicit axis range")


def date(value, path):
    text(value, path)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        fail(path, "expected a YYYY-MM-DD date")
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        fail(path, "not a valid calendar date")


def url(value, path):
    text(value, path)
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            fail(path, "expected a direct HTTP/HTTPS source URL without credentials")
        parsed.port
    except ValueError:
        fail(path, "invalid URL")
    if any(ord(char) <= 32 for char in value):
        fail(path, "URL cannot contain whitespace or control characters")


def validate(data):
    obj(data, "report", {"version", "id", "language", "publication", "edition", "date", "title", "lead", "intro", "metrics", "sections", "conclusion", "footerNote"})
    if type(data.get("version")) is not int or data["version"] != 1:
        fail("version", "only integer version 1 is supported")
    date(data.get("date"), "date")
    for key in ("title", "lead"):
        text(data.get(key), key)
    for key in ("language", "publication", "edition", "footerNote"):
        if key in data:
            text(data[key], key, required=False)
    if "id" in data and (not isinstance(data["id"], str) or not re.fullmatch(r"[A-Za-z0-9-]{1,80}", data["id"])):
        fail("id", "expected 1-80 ASCII letters, digits, or hyphens")
    optional_texts(data, "report", ("intro",))
    metrics = data.get("metrics", [])
    if not isinstance(metrics, list) or len(metrics) > 4:
        fail("metrics", "expected an array of 0-4 metrics")
    for i, metric in enumerate(metrics):
        p = f"metrics[{i}]"
        obj(metric, p, {"value", "label", "note"})
        for key in ("value", "label"):
            text(metric.get(key), f"{p}.{key}")
        if "note" in metric:
            text(metric["note"], f"{p}.note", required=False)
    sections = data.get("sections")
    if not isinstance(sections, list) or not sections:
        fail("sections", "at least one section is required")
    for i, section in enumerate(sections):
        p = f"sections[{i}]"
        obj(section, p, {"title", "intro", "paragraphs", "items", "table", "charts"})
        text(section.get("title"), f"{p}.title")
        if "intro" in section:
            text(section["intro"], f"{p}.intro", required=False)
        optional_texts(section, p, ("paragraphs",))
        items = section.get("items", [])
        if not isinstance(items, list):
            fail(f"{p}.items", "expected an array of entries")
        for j, item in enumerate(items):
            q = f"{p}.items[{j}]"
            obj(item, q, {"title", "tag", "lead", "paragraphs", "bullets", "sources"})
            text(item.get("title"), f"{q}.title")
            for key in ("tag", "lead"):
                if key in item:
                    text(item[key], f"{q}.{key}", required=False)
            optional_texts(item, q, ("paragraphs", "bullets"))
            if not any(item.get(key) for key in ("lead", "paragraphs", "bullets")):
                fail(q, "requires content in lead, paragraphs, or bullets")
            sources = item.get("sources", [])
            if not isinstance(sources, list):
                fail(f"{q}.sources", "expected an array of sources")
            for k, source in enumerate(sources):
                r = f"{q}.sources[{k}]"
                obj(source, r, {"label", "url", "date"})
                text(source.get("label"), f"{r}.label")
                url(source.get("url"), f"{r}.url")
                if "date" in source:
                    date(source["date"], f"{r}.date")
        table = section.get("table")
        if table is not None:
            obj(table, f"{p}.table", {"caption", "headers", "rows"})
            if "caption" in table:
                text(table["caption"], f"{p}.table.caption")
            headers = table.get("headers")
            texts(headers, f"{p}.table.headers")
            if not 2 <= len(headers) <= 6:
                fail(f"{p}.table.headers", "requires 2-6 columns")
            rows = table.get("rows")
            if not isinstance(rows, list) or not rows:
                fail(f"{p}.table.rows", "at least one row is required")
            for j, row in enumerate(rows):
                texts(row, f"{p}.table.rows[{j}]")
                if len(row) != len(headers):
                    fail(f"{p}.table.rows[{j}]", "cell count does not match the headers")
        charts = section.get("charts", [])
        if not isinstance(charts, list):
            fail(f"{p}.charts", "expected an array of charts")
        for j, value in enumerate(charts):
            chart(value, f"{p}.charts[{j}]")
        if not (items or section.get("paragraphs") or table or charts):
            fail(p, "section requires entries, paragraphs, a table, or charts")
    if "conclusion" in data:
        c = obj(data["conclusion"], "conclusion", {"title", "paragraphs"})
        text(c.get("title"), "conclusion.title")
        texts(c.get("paragraphs"), "conclusion.paragraphs")
        if not c["paragraphs"]:
            fail("conclusion.paragraphs", "at least one paragraph is required")
    return data


def embedded_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def load_locales(directory):
    locales = json.loads((directory / "assets" / "locales.json").read_text(encoding="utf-8"))
    obj(locales, "locales", UI_LANGUAGES)
    for language in UI_LANGUAGES:
        path = f"locales.{language}"
        entry = obj(locales.get(language), path, UI_TEXT_KEYS | {"aliases", "themes", "fonts"})
        for key in UI_TEXT_KEYS:
            text(entry.get(key), f"{path}.{key}")
        texts(entry.get("aliases"), f"{path}.aliases")
        if not entry["aliases"]:
            fail(f"{path}.aliases", "at least one language alias is required")
        for key, choices in (
            ("themes", ("paper", "white", "sage", "night")),
            ("fonts", ("editorial", "modern", "serif")),
        ):
            values = obj(entry.get(key), f"{path}.{key}", choices)
            for choice in choices:
                text(values.get(choice), f"{path}.{key}.{choice}")
    return locales


def resolve_ui_language(language, locales):
    tag = language.strip().replace("_", "-").lower()
    selected, specificity = "en", -1
    for name, entry in locales.items():
        for alias in entry["aliases"]:
            alias = alias.lower()
            if (tag == alias or tag.startswith(alias + "-")) and len(alias) > specificity:
                selected, specificity = name, len(alias)
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--theme", choices=("paper", "white", "sage", "night"), default="paper")
    parser.add_argument("--font", choices=("editorial", "modern", "serif"), default="editorial")
    parser.add_argument("--language", choices=UI_LANGUAGES, help="override report/editor language; does not translate supplied text")
    parser.add_argument("--force", action="store_true", help="allow replacing the specified output file")
    args = parser.parse_args()
    try:
        data = validate(json.loads(args.input.read_text(encoding="utf-8")))
        data["language"] = args.language or (data.get("language") or "").strip() or "en"
        directory = Path(__file__).resolve().parents[1]
        locales = load_locales(directory)
        ui_language = resolve_ui_language(data["language"], locales)
        ui = locales[ui_language]
        # Explicit legacy locales keep their revisions; overrides and new defaults affect the digest.
        digest = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        data.setdefault("id", f"report-{digest[:16]}")
        data.setdefault("publication", ui["publication"])
        state = {"data": data, "appearance": {"theme": args.theme, "font": args.font, "editing": True}, "revision": digest, "updatedAt": 0}
        template = (directory / "assets" / "report-template.html").read_text(encoding="utf-8")
        for marker in ("__REPORT_STATE_JSON__", "__REPORT_LOCALES_JSON__"):
            if template.count(marker) != 1:
                raise InvalidReport(f"template marker {marker} must appear exactly once")
        if args.output.resolve() == args.input.resolve():
            raise InvalidReport("output cannot overwrite the input JSON")
        if args.output.exists() and not args.force:
            raise InvalidReport("output already exists; choose a new path or use --force after confirming replacement")
        replacements = {
            "__REPORT_STATE_JSON__": embedded_json(state),
            "__REPORT_LOCALES_JSON__": embedded_json(locales),
            "__REPORT_LANGUAGE__": escape(data["language"].replace("_", "-"), quote=True),
            "__UI_LANGUAGE__": ui_language,
            "__REPORT_TITLE__": escape(data["title"]),
        }
        for key in UI_TEXT_KEYS:
            marker = "__UI_" + re.sub(r"(?<!^)(?=[A-Z])", "_", key).upper() + "__"
            replacements[marker] = escape(ui[key], quote=True)

        def replace_marker(match):
            marker = match.group(0)
            if marker not in replacements:
                raise InvalidReport(f"unknown template marker: {marker}")
            return replacements[marker]

        # One pass avoids substituting marker-like text inside user content.
        html = re.sub(r"__[A-Z0-9_]+__", replace_marker, template)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.output.parent, prefix=".report-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(html)
        try:
            os.replace(temporary, args.output)
        finally:
            temporary.unlink(missing_ok=True)
        print(f"Generated: {args.output.resolve()}")
    except (InvalidReport, OSError, json.JSONDecodeError) as error:
        print(f"Generation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
