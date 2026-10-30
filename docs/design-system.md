# UI Design System Brief

This brief turns the design doc into concrete UI rules for the Next.js build. It is intentionally specific so independent implementers produce a coherent product.

## Brand feel

A calm, trustworthy regulatory console: deep ink navigation, warm off-white canvas, teal action color, amber/red reserved for review states. Dense data without visual noise. No gradients, glassmorphism, neon, or generic purple SaaS styling.

## Tokens

| Token | Value | Use |
|---|---|---|
| `--color-ink` | `#0B1F33` | Sidebar, headings, primary text |
| `--color-ink-soft` | `#33475B` | Secondary text |
| `--color-canvas` | `#F5F7FA` | Page background |
| `--color-surface` | `#FFFFFF` | Cards, dialogs |
| `--color-surface-muted` | `#EEF2F5` | Table headers, subtle panels |
| `--color-primary` | `#0F766E` | Primary buttons, active nav, links |
| `--color-primary-dark` | `#115E59` | Hover |
| `--color-primary-soft` | `#CCFBF1` | Selected rows, soft tags |
| `--color-accent` | `#B45309` | Warnings, pending review |
| `--color-accent-soft` | `#FEF3C7` | Warning backgrounds |
| `--color-danger` | `#B42318` | Errors, destructive/deny |
| `--color-danger-soft` | `#FEE4E2` | Error backgrounds |
| `--color-success` | `#15803D` | Accepted/active only |
| `--color-success-soft` | `#DCFCE7` | Success backgrounds |
| `--color-border` | `#DDE3EA` | Borders/dividers |
| `--radius-sm` | `8px` | Inputs, tags |
| `--radius-md` | `12px` | Cards, panels |
| `--radius-lg` | `16px` | Dialogs, hero panels |
| `--shadow-card` | `0 1px 2px rgb(11 31 51 / 0.04), 0 8px 24px rgb(11 31 51 / 0.04)` | Cards |
| `--shadow-pop` | `0 18px 48px rgb(11 31 51 / 0.16)` | Dialogs/dropdowns |

Typography:

- Display: **Sora** (600/700), letter-spacing `-0.02em`.
- Body/UI: **Public Sans** (400/500/600), 14–16 px.
- Data/table numerics: Public Sans with `font-variant-numeric: tabular-nums`.
- Page title 28–32 px; section title 18–20 px; eyebrow 11–12 px uppercase tracking `0.08em`.
- Line height: body 1.55; headings 1.15.

Spacing: 4 px base; page gutters 24 px desktop / 16 px mobile; card padding 20–24 px; section gap 24–32 px.

## Layout

- Desktop: fixed 264 px ink sidebar; topbar 64 px; content max-width 1440 px with 24 px gutters.
- 1024–1279 px: 232 px sidebar.
- <1024 px: sidebar becomes a keyboard-accessible drawer; topbar keeps menu, page title, notifications, user.
- Mobile <640 px: stacked cards, horizontally scrollable table regions with visible scroll hint, 16 px gutters.
- Persistent demo ribbon at the very top of every authenticated page and login; public verify page shows a demo notice in the result card.
- Sidebar nav grouped with 11–12 px uppercase group labels. Active item: teal-soft background, teal left indicator, white/ink text.
- Topbar: breadcrumb/page context, academic-year selector where relevant, notification bell with unread dot, user menu with role and sign-out.

## Components

### Buttons

- Primary: teal fill, white text, 40 px height, 8 px radius.
- Secondary: white fill, ink border, ink text.
- Ghost: transparent, ink text, subtle hover.
- Danger: danger fill only for irreversible actions; otherwise danger outline.
- Icon button: 40×40 px, tooltip with accessible name.
- Loading: spinner + verb (“Validating…”); disabled while pending.

### Status chips

Never one “Verified” badge. Variants:

- Identity: `MISSING` gray, `MALFORMED` red, `FORMAT_VALID` blue, `PENDING_EXTERNAL_CHECK` amber, `EXTERNALLY_CONFIRMED` green **plus** “Mock/sandbox” tag, `EXTERNAL_MISMATCH` red, `EXTERNAL_UNAVAILABLE` gray, `MANUAL_REVIEW` amber, `CORRECTED` blue.
- Batch: DRAFT gray, VALIDATING blue, VALIDATION_FAILED red, READY_FOR_ATTESTATION amber, SUBMITTED/UNDER_AICTE_REVIEW blue, RETURNED amber, ACCEPTED green, REJECTED red.
- Capacity: within regular green, within + supernumerary blue, possible excess amber (not red until reviewed), missing approval gray, pending rule review amber.
- Severity: INFO gray, WARNING amber, HIGH orange/red, ERROR red.
- Mock: dashed border amber chip with flask icon and text “Mock/sandbox”.

Chips use icon + text; color is never the only signal.

### Cards and KPI

- Card: white, 1 px border, 12 px radius, card shadow, 20–24 px padding.
- KPI: eyebrow, 28–32 px value, delta/hint, optional sparkline/icon. Max 4 per row desktop, 2 tablet, 1 mobile.
- Alert card: left 3 px colored border, icon, title, body, action link.
- Empty state: line illustration/icon, title, one-sentence explanation, primary action.

### Tables

- Header: muted background, 12 px uppercase eyebrow, sortable arrows, sticky within scroll container.
- Rows: 56–64 px, hover, selected state teal-soft, divider border.
- First column can include avatar/initials + primary/secondary text.
- Right-align numeric columns with tabular nums.
- Row actions in a kebab menu or explicit text link; destructive actions separated.
- Pagination: “Showing 1–20 of 143”, page size selector, previous/next.
- Mobile: keep critical columns, allow horizontal scroll within a labelled region; optional card list for cases/students.

### Forms

- Labels above fields, 12–13 px medium ink; required marker; helper text below.
- Inputs 40–44 px, 1 px border, 8 px radius, teal focus ring.
- Errors: red border + icon + message linked with `aria-describedby`; summary at top for long forms.
- Two-column grids on desktop, single column mobile.
- Destructive/irreversible actions require a confirmation dialog with the consequence stated in plain language.
- Multi-step wizards: stepper header (numbered circles/labels), current step teal, completed with check, future muted; back/next fixed at bottom of card.

### Dialogs, drawers, toasts

- Dialog max-width 560 px (forms 720 px); title + description; close button; footer actions right-aligned.
- Drawer 420–520 px from right for details; full-screen mobile.
- Toasts top-right, 4 s, one at a time, with action where useful; errors persist longer and include a support reference/trace ID.
- Never use a toast as the only place a validation error appears.

### Charts

- Recharts; no 3D, no gradients, minimal gridlines.
- Palette: teal primary, ink secondary, amber warning, red error, gray neutral.
- Always include axis labels/units; legends for >2 series; tooltip with exact values.
- Provide an accessible text summary and a “View as table” toggle.
- Donut center shows total; segments labelled in legend with counts.

### Public verification page

- Centered 720 px card on canvas; minimal header with government-style typographic mark (text, not official emblem).
- Top: result status (“Verification reference valid” vs “Reference unavailable”).
- Demo/mock banner prominent.
- Recipient/purpose/expiry summary.
- Claim cards: label, value, source chip, status, “as of”.
- Receipt download (JSON) + signature/key ID.
- Print stylesheet: white background, hide controls, show URL + printed-at timestamp.
- Denied state: no hint about whether a record exists; generic copy + support route.

## Copy rules

- Plain language, active voice, sentence case.
- “APAAR format valid” vs “APAAR externally confirmed (mock)” vs “Record accepted by AICTE” vs “Credential verified” are distinct phrases.
- Do not say “verified student” or “verified degree”.
- Use “possible excess” until a reviewer decides.
- Explain next actions: “Correct the APAAR ID, then revalidate.”
- Error messages include what happened, why, and what to do next.
- Never put student names or identifiers in notification titles, email subjects, or URLs.

## Accessibility rules

- Skip link; semantic landmarks; one `h1` per page.
- Focus visible; dialogs trap focus and restore it on close.
- Tables have captions; sortable headers `aria-sort`.
- Charts have text alternatives.
- Status chips include text.
- Minimum 44 px touch targets.
- Respect `prefers-reduced-motion`.
- Contrast ≥4.5:1 for body, ≥3:1 for large text/UI.

## Page composition notes

- **Login:** split 55/45; left ink panel with product promise and three proof points (privacy, explainable rules, controlled verification); right white card with form and demo account chips. No stock photos.
- **Institution dashboard:** page header with year selector + “New batch” primary; KPI row; two-column main (capacity by programme table, identity donut); recent batches + unresolved cases; alerts.
- **Students:** filter bar in a card; table with masked APAAR, programme, year, status, identity, flags; row click to detail.
- **Batch wizard:** single card; stepper; dropzone with file requirements; validation summary (3 counts + status) above findings table; attestation panel with declaration; receipt modal.
- **AICTE dashboard:** KPI row; intake vs enrolment bar/line; review backlog and possible excess panels; institution table; quality trend.
- **Review detail:** sticky decision panel on desktop (right 360 px), evidence main column; mobile decision panel below summary.
- **Reports:** filter bar, tabs, generated-at note, table, export button with audit notice; suppression callout.
- **Audit:** dense table with filter row; detail drawer.
- **Student:** identity card with masked APAAR and distinct status chips; share list; create-share wizard; QR dialog.
- **Verification:** claim cards; receipt; denial state.
