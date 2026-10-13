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

These forms can be combined. A section may also have an optional `intro` string.

Each entry requires `title` and at least one of `lead`, `paragraphs`, or `bullets`. `lead` is an emphasized main point; the latter two are string arrays. An optional `tag` labels a category.

Entries may include `sources`, an array of `{label, url, date?}`. A URL must be a direct HTTP/HTTPS source link without embedded credentials. An optional date must be a valid calendar date. Providing a link is not fact-checking: read the source and confirm that it supports the claim.

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

The HTML's `script#reportState` contains `{data, appearance, revision, updatedAt}`. Extract and edit `data`, then render it again. Preserve the ID, language, source links, and appearance. Pass the existing theme and font through the CLI to retain them.

The renderer recomputes the revision to keep stale drafts from replacing newer content. Explicit language overrides are included in that revision. Existing report IDs and the `editorial-report:v1:` browser storage namespace are retained.

The embedded `script#reportLocales` contains the UI catalog. The exported HTML does not fetch translation files at runtime. Older reports without this block can still be edited by extracting their `reportState` data and rendering it with the current template.

By default, the renderer refuses to overwrite an existing output. Use `--force` only when the user has authorized that replacement. It does not access the network, fetch news, translate prose, or modify the input JSON.
