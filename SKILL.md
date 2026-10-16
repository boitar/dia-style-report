---
name: dia-style-report
description: "Create or edit unofficial Dia-inspired, editorial-style single-file HTML reports for news briefs, tool comparisons, research, and reference summaries. Reports support inline text editing, interactive bar charts, themes, saving, and multilingual interfaces. Use for report deliverables, not ordinary answers or full websites."
---

# Dia Style Report

Turn a question or source material into a conclusion-first HTML report that can be read and edited directly in a browser. Use warm-paper colors, serif headings, fine rules, and restrained labeled entries by default. This is an independent, unofficial implementation inspired by observable Dia document styles; it does not require Dia or an online frontend service.

## Content and layout

A short question can justify a complete report. Infer a reasonable report type and scope; ask only about missing conditions that materially change the conclusion, and complete independent work first. Explicit skill invocation defaults to HTML delivery unless the user asks for another format or text only.

- **Tool comparisons**: give a conditional recommendation, then compare dimensions, differences, suitable audiences, and migration costs. Do not invent scores for visual effect.
- **News briefs**: identify a common thread and group stories by topic. Distinguish the report date from event dates; put only supported figures in the metrics strip.
- **Research**: give the conclusion and its boundaries before explaining evidence, mechanisms, and implications. Mix prose and entries when helpful.
- **Reference summaries**: preserve important relationships, constraints, and terminology; choose components to fit the material.

These are layout criteria, not mandatory chapter templates. Let content determine titles, sections, tables, and metrics. Omit unsupported metrics and do not pad short reports.

When comparable numeric data supports a chart, use `sections[].charts` for horizontal rankings or vertical indicator comparisons. Read the chart contract in the [data specification](references/report-data.md). Keep dimensions and units clear; supplementary text such as cost belongs in each point's tooltip details, not an invented second axis. Do not estimate exact values from a reference image. Label fictional demonstrations explicitly. Point order follows the input; `tone` has no built-in factual meaning.

For changeable claims such as current capabilities, pricing, or news, use available research tools to read direct sources. Match source labels to URLs and state important event dates. Separate facts, vendor claims, and editorial judgments. Without research access, preserve the supplied facts and disclose the scope rather than presenting them as a current verified survey.

## Language

Choose the report language before writing its content:

- Follow the user's explicit output-language request, even when this skill, the examples, or the source material use a different language. English instructions do not imply English output.
- When editing an existing report without a language-change request, retain its language. For a new report with no requested output language, use English.
- Use `en` for English, `zh-CN` for Simplified Chinese, `ja` for Japanese, and `zh-TW` for Traditional Chinese. Keep Simplified and Traditional Chinese distinct.

Write all authored report text in that language: publication and edition labels, titles, introductory text, metrics labels and notes, section and entry text, table captions and cells, conclusions, and footer notes. Keep proper names, accurately identified sources, and intentional original-language quotations intact; preserve source URLs, dates, and factual meaning. Do not copy example prose in the wrong language.

Set `data.language` to match the written content. If using `--language`, pass the same target language. The renderer localizes controls, feedback, dates, and font stacks; it does not translate supplied prose. When the user asks to translate an existing report, translate its authored text as well as changing its language metadata; changing the flag alone is insufficient.

For example, a request to produce a Japanese brief from English articles requires Japanese report text and `"language": "ja"`, not English paragraphs with Japanese controls.

Before delivery, check that the report text, `script#reportState` language, and editor locale match the requested output language. Regional and script aliases are described in the data specification. For another explicitly requested language, write the content in that language and use an appropriate language tag; disclose that the built-in editor UI falls back to English.

## Generate a report

Read the [data specification](references/report-data.md) for first-time generation and prepare plain-text JSON. Read the [design reference](references/design.md) when adjusting visual style.

Run the script relative to the skill directory actually loaded:

```bash
python3 /path/to/dia-style-report/scripts/render_report.py --input /absolute/path/report.json --output /absolute/path/report.html
```

The script uses Python's standard library to validate data and embed content, CSS, interactions, and the locale catalog into a portable HTML file. Keep the JSON for later edits without requiring the reader to work with JSON. If script execution is unavailable, follow the template and disclose which checks were not run.

Reuse `assets/report-template.html` instead of rebuilding CSS for each report. User-specified styles take precedence; keep typography, color, and spacing consistent. These presets are this skill's implementation, not an exact recovery of Dia's original presets.

## Edit existing reports

Read the existing HTML's `script#reportState` first. Preserve current text, sources, ID, language, and appearance before applying the requested changes. An exported HTML snapshot already contains browser edits; do not overwrite those edits with stale JSON.

Retain appearance with `--theme paper|white|sage|night`, `--font editorial|modern|serif`, and `--badge-tilt on|off` (default `on`). Map an existing `appearance.badgeTilt: false` to `--badge-tilt off`; a missing field defaults to enabled. Use `--force` only to replace a file the user explicitly asked to modify. Avoid overwriting names when creating new reports.

## Interactions and delivery

Headings, paragraphs, entries, metrics, table text, and chart titles/descriptions/captions are editable. Change chart points, axes, and tooltip details through the input JSON and regenerate; there is no in-page chart-data editor. Dates and source links remain reading elements. The bottom-right gear opens appearance and saving controls. Font stacks are local and depend on the device.

Category labels use fine outlines and a stable subtle tilt by default. The gear menu can turn label tilt off without changing content. Title and label share a line when they fit; long labels wrap fully and stay horizontal. Editing text, undo, and appearance changes do not reassign angles. Drafts, saved HTML, and printing retain the toggle. Existing HTML needs regeneration with the current template to gain this feature; first preserve its current data and appearance.

Charts use inline SVG with no runtime network dependency. Hover or keyboard focus displays point details; click/tap, Enter, or Space pins or closes them, and Escape dismisses. Tooltips remain available when the pointer enters them. Narrow screens stack chart explanations above figures; dense labels scroll within the figure, never the whole page. Nonzero axis baselines are visibly disclosed. Saving HTML preserves charts and edited prose but clears temporary tooltip state. Printing keeps static charts and hides tooltips; tooltip-only details are not printed.

Support desktop and mobile by default: narrow-screen entries are single-column, metrics use at most two columns, tables become labeled rows, and mobile settings use a scrollable bottom sheet. Preserve safe areas, 44px controls, a reachable close button, backdrop dismissal, and browser zoom. Do not simulate mobile layout by shrinking the desktop page.

Drafts use the current browser's available local storage and do not replace disk files. Save HTML downloads a self-contained file with current text, language, theme, font, and label-tilt setting; reopening it permits further editing. Editing and downloading must remain available when storage is unavailable. Never claim that edits automatically update the original file.

Before delivery, run data validation. When previewing is possible, check the chosen language on desktop, at 320px and 390px, and in landscape. Confirm no horizontal overflow, complete titles and table text, scrollable settings with a visible close button, editing, theme/font changes, and export/reopen behavior. Closing settings must restore report interactions. Report only checks actually completed; viewport simulation is not physical-device or Safari validation.

For reports containing category labels, also check the tilt toggle, stable angles after editing/export, and horizontal full-text wrapping for long labels.

For reports containing charts, also check keyboard/touch details, tooltip viewport bounds, long labels, and export/reopen with the chart data intact. Use the labeled fictional chart example when demonstrating visual behavior rather than presenting it as a current model or price comparison.

Deliver an openable HTML file, the skill entry point, and one invocation example. Present the report first and state necessary limitations. Keep skill-development notes out of the report itself.
