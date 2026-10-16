# Report data specification v1

All text fields are plain text, not HTML or Markdown. The renderer and page handle structure, emphasis, and source display. Omit unnecessary components rather than inventing numbers or recommendations.

## Top-level fields

| Field | Constraint / purpose |
| --- | --- |
| `version` | Required integer `1` |
| `id` | Optional; 1-80 ASCII letters, digits, or hyphens. The renderer can generate a stable ID from content. |
| `language` | Optional; defaults to `en` for new reports. See language behavior below. |
| `publication` | Optional; defaults to a localized "Research report" label. Shown at the left of the publication header. |
| `edition` | Optional text next to the date |
| `date` | Required valid `YYYY-MM-DD` date, chosen according to the user's time zone |
| `title` | Required report headline |
| `lead` | Required one-sentence conclusion, displayed with stronger emphasis |
| `intro` | Optional string array providing context |
| `metrics` | Optional array of 0-4 `{value, label, note?}` objects; use supported numbers only |
| `sections` | Required nonempty section array |
| `conclusion` | Optional `{title, paragraphs}` with a nonempty `paragraphs` array |
| `footerNote` | Optional scope, limitations, or other necessary notes |

## Languages

Use `en`, `zh-CN`, `ja`, or `zh-TW` for the four built-in editor languages. The locale controls button labels, theme and font names, accessibility text, status messages, date formatting, and local font fallbacks.

The optional `--language en|zh-CN|ja|zh-TW` CLI flag overrides `language` in the input. Without it, a nonblank input language is preserved; missing or blank language values default to English. Existing explicit `zh-CN` data continues to generate Simplified Chinese controls.

Regional and script tags use the closest built-in UI: for example, `en-GB` uses English, `ja-JP` uses Japanese, `zh-Hans` uses Simplified Chinese, and `zh-Hant` or `zh-HK` uses Traditional Chinese. Matching is case-insensitive; underscores are treated as hyphens for locale selection.

Other tags use English controls. Valid language tags still format dates and identify the report language; malformed tags fall back to the selected UI locale in the browser. Dates are formatted in UTC to preserve the supplied calendar date across device time zones.

**Setting a language does not translate content.** Provide the headline, paragraphs, table cells, and source labels in the intended language. For example, setting `"language": "ja"` on English paragraphs changes the editor and date format, not the paragraphs.

## Sections and entries

Every section requires a `title` and at least one content form:

- `paragraphs`: a string array for continuous analysis.
- `items`: an entry array for categorized points, news, or tool descriptions.
- `table`: `{caption?, headers: [column names], rows: [[cell text]]}`. Use 2-6 columns; every row must match the header count.
- `charts`: an array of the bar-chart objects described below.

These forms can be combined. A section may also have an optional `intro` string.

Each entry requires `title` and at least one of `lead`, `paragraphs`, or `bullets`. `lead` is an emphasized main point; the latter two are string arrays. An optional `tag` labels a category.

Category labels use fine outlines with stable subtle tilt by default. Title and tag share a line when they fit; a tag that needs multiple lines keeps all its text and stays horizontal. Use the gear menu's label-tilt checkbox or CLI `--badge-tilt on|off` (default `on`) to control this appearance. No new entry/content fields are needed.

Entries may include `sources`, an array of `{label, url, date?}`. A URL must be a direct HTTP/HTTPS source link without embedded credentials. An optional date must be a valid calendar date. Providing a link is not fact-checking: read the source and confirm that it supports the claim.

## Interactive bar charts

A chart can be the section's only content. Charts appear after any section prose, table, and entries. They are self-contained SVG figures; the generated HTML does not fetch a library or data.

| Field | Constraint / purpose |
| --- | --- |
| `type` | Required `horizontal-bar` or `vertical-bar` |
| `title` | Required plain-text heading, editable in the HTML |
| `description` | Required plain-text explanation, editable in the HTML |
| `caption` | Required plain-text figure caption, editable in the HTML |
| `valueLabel` | Required name/unit of the plotted numeric dimension |
| `points` | Required nonempty array, displayed in input order |
| `axis` | Optional `{min, max, step?}`; bounds required when this object is present |

Each point requires `label` (its full, nonempty name) and `value` (a finite, nonnegative JSON number, not a boolean or numeric string). Optional `tone` is `primary` (default) or `muted`; it changes the gray treatment, not the data's meaning. Explain any grouping in the prose/caption. Optional `details` is an array of nonempty plain-text `{label, value}` pairs; values such as `"$1.20 (illustrative)"` are text, not another plotted series.

Without `axis`, the axis starts at zero and uses automatic upper bounds/ticks. An all-zero dataset uses a 0-1 axis so it remains readable. Explicit bounds must be finite and nonnegative, `max > min`, and contain every point, including values exactly at either boundary. Optional `step` must be finite and positive, producing no more than 100 intervals. Data outside explicit bounds is rejected rather than clipped. A nonzero minimum always produces a localized baseline notice; bar length then represents only the difference above that minimum.

```json
{
  "title": "I. Compare illustrative options",
  "charts": [
    {
      "type": "vertical-bar",
      "title": "An illustrative indicator",
      "description": "Fictional data; hover, tap, or focus a bar for details.",
      "caption": "Not a real product evaluation or quote.",
      "valueLabel": "Score",
      "points": [
        {"label": "Option A", "value": 56, "details": [{"label": "Task cost", "value": "$1.20 (example)"}]},
        {"label": "Option B", "value": 52, "tone": "muted"}
      ]
    }
  ]
}
```

Update point labels, numbers, details, or axes in JSON and regenerate; they are not inline-editable. Titles, descriptions, and captions use the existing draft/undo/export behavior. Saved HTML embeds all chart data and rebuilds interactive figures on reopen. Printing keeps the static figure and baseline notice, but hides overlays; tooltip-only details are not included in the printed chart.

## Minimal complete example

```json
{
  "version": 1,
  "language": "en",
  "publication": "Research notes",
  "date": "2026-10-13",
  "title": "Make the conclusion clear first",
  "lead": "Answer the reader's question before presenting supporting material.",
  "intro": ["Keep the visual language consistent, but let the question determine the structure."],
  "sections": [
    {
      "title": "I. Understand the reader's decision",
      "items": [
        {
          "title": "Choosing between options",
          "tag": "Comparison",
          "lead": "Compare meaningful differences and costs.",
          "paragraphs": ["Explain when the recommendation applies and what could change it."],
          "bullets": ["Use common comparison dimensions.", "Include migration costs."]
        }
      ]
    }
  ]
}
```

## Editing exported reports

The HTML's `script#reportState` contains `{data, appearance, revision, updatedAt}`. Extract and edit `data`, then render it again. Preserve the ID, language, source links, and appearance. Pass the existing theme, font, and label-tilt setting through the CLI to retain them.

`appearance` contains `theme`, `font`, `editing`, and `badgeTilt`. The new `badgeTilt` field is a boolean, defaults to `true`, and also defaults to enabled when absent from an older state. Pass `--badge-tilt off` for `false` and `--badge-tilt on` for `true` when regenerating. Text-editing availability remains an in-page control. Browser drafts and Save HTML retain the label-tilt selection; exporting still works when local storage is unavailable. Printing follows that selection. Existing HTML does not gain the control automatically.

Angles are derived from the preserved report ID and item path, not tag text, and do not change during inline edits or export/reopen. JSON reordering assigns them by the new positions. If the ID is omitted when regenerating changed JSON, a newly generated ID can change the angles too.

The renderer recomputes the revision to keep stale drafts from replacing newer content. Explicit language overrides are included in that revision. Existing report IDs and the `editorial-report:v1:` browser storage namespace are retained.

The embedded `script#reportLocales` contains the UI catalog. The exported HTML does not fetch translation files at runtime. Older reports without this block can still be edited by extracting their `reportState` data and rendering it with the current template.

By default, the renderer refuses to overwrite an existing output. Use `--force` only when the user has authorized that replacement. It does not access the network, fetch news, translate prose, or modify the input JSON.
