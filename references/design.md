# Design reference

This unofficial design was reimplemented from the user's single-file Dia technology-brief sample. It aims for a contemporary editorial reading experience and the requested editing and appearance controls. It is not an export of Dia's complete CSS, runtime scripts, or original presets.

## Visual structure

- Maximum content width: 760px. Desktop page padding: 48px 20px 96px.
- A compact publication header leads into a conclusion-first introduction. The serif headline uses weight 500 and a responsive 34-52px size.
- Section headings are 21px with a 2px ink-colored rule. Entries are separated by light 1px rules.
- Entries use a 170px label column, a 24px gap, and the remaining width for explanations. At 620px and below, they become single-column.
- Body text is explicitly 16px with line-height 1.75. Introductory text is 17px; notes are at least 12px.
- A metrics strip distributes 1-4 actual metrics evenly and uses at most two columns on narrow screens. Omit it when the content has no reliable numbers.
- Tables compare genuine dimensions. On narrow screens, rows become labeled entries without dropping any text.
- Report content uses square corners, fine rules, and whitespace. The gear and settings panel are controls, so modest rounding and depth are appropriate.

## Presets

| Theme | Paper | Main text | Secondary text | Notes | Rules |
| --- | --- | --- | --- | --- | --- |
| Paper `paper` (default) | #f4f1ea | #1c1a17 | #55504a | #6c655c | #d8d2c6 |
| White `white` | #ffffff | #202020 | #505050 | #686868 | #dddddd |
| Sage `sage` | #edf1ed | #202923 | #48564c | #58665c | #c7d1c9 |
| Night `night` | #20221f | #eeeee7 | #c5c8bf | #b0b5a8 | #50564c |

The default paper theme uses darker notes than the reference sample to improve small-text readability. Semantic CSS variables update report content, controls, and status messages together.

| Font preset | Headings / numbers | Body |
| --- | --- | --- |
| Editorial `editorial` (default) | Locale-appropriate serif stack | Locale-appropriate sans-serif stack |
| Modern `modern` | Locale-appropriate sans-serif stack | Locale-appropriate sans-serif stack |
| Serif `serif` | Locale-appropriate serif stack | Locale-appropriate serif stack |

English favors Georgia for headings. Simplified Chinese uses Songti-style headings; Traditional Chinese uses Traditional Chinese serif fallbacks; Japanese uses Mincho-style headings and Gothic-style body fonts. These are local font stacks, not bundled fonts. Exact glyphs vary by device. There are no remote fonts or CDN dependencies.

## Language behavior

The report's `language` selects editor labels, accessibility descriptions, status messages, date formatting, and the font stack. The four built-in UI languages are `en`, `zh-CN`, `ja`, and `zh-TW`; new reports default to English. The shared text catalog is [assets/locales.json](../assets/locales.json), embedded into each generated HTML file.

Language settings do not translate supplied paragraphs, source labels, or table cells. Write report content in the requested language before rendering. Supported regional and script aliases select the corresponding UI; other language tags use the English UI. Valid report language tags still control date formatting and the document's language metadata.

## Interaction boundaries

At 620px and below, use single-column content, 30-38px headlines, 16px body and table text, and a separate date line. Tables pair dimension labels with content; at 360px and below, place the labels above the content. Hidden column headings retain table semantics. Page margins, the gear, and the panel allow for device safe areas. The viewport must not disable zoom.

Mobile settings use a bottom sheet with a persistent 44px close button and an independently scrollable content area. Short landscape screens use the same sheet. Theme, font, editing, and saving controls are at least 44px, with 8px between theme buttons. Opening the sheet locks background scrolling and focus; closing it or clicking the backdrop restores the report. Escape closes it and returns focus to the gear. Desktop uses the bottom-right popover.

Each text block is independently editable. Paste inserts plain text and preserves structure and source links. Paragraphs may contain line breaks; Enter ends single-line heading edits. Text and panel controls are keyboard-focusable.

Drafts are isolated by report ID and content revision. Keep the existing `editorial-report:v1:` storage namespace for compatibility. Export a structured snapshot of current text and appearance, clear temporary editing DOM and background locks, and rebuild from the snapshot on reopen. An older browser draft must not overwrite a newer exported snapshot. The locale catalog is embedded too, so exported reports remain editable offline.

Printing hides controls and edit outlines. Section headings stay with following content, and entries should avoid splitting when practical; long sections may paginate normally. Night mode prints with a white background and dark text. Actual background printing still depends on browser settings.
