# Accessibility Notes (Prototype)

Target: WCAG 2.1 AA intent for key user journeys, subject to applicable government accessibility standards.

## Implemented intent

- Semantic landmarks (`header`, `nav`, `main`, `aside`, `footer`) in the portal shell.
- Skip-to-content link as the first focusable element.
- Visible focus rings on all interactive elements (≥3:1 contrast).
- Form labels are programmatically associated; errors are announced with `aria-live` and linked to fields.
- Dialogs use Radix focus trapping, `Escape` to close, and title/description wiring.
- Tables have captions and column scopes; sortable headers expose `aria-sort`.
- Status is never conveyed by color alone: every status chip has text and an accessible label.
- Charts include a text summary/table fallback and `role="img"` descriptions.
- Reduced motion is respected via `prefers-reduced-motion`.
- Touch targets ≥44×44 px on mobile.
- Text contrast ≥4.5:1 (large text ≥3:1); focus indicators ≥3:1.
- Public verification page is print-friendly and does not rely on hover.

## Manual checklist

- [ ] Tab through login, dashboard, upload wizard, decision panel, share wizard, and public result page.
- [ ] Complete the upload wizard with a keyboard only.
- [ ] Screen reader announces validation errors and status changes.
- [ ] 390 px, 768 px, 1024 px, 1440 px layouts usable without horizontal page scroll (tables may scroll within a labelled region).
- [ ] Zoom to 200% does not lose content or controls.
- [ ] Color-blind simulation: status chips still distinguishable by text/icon.
- [ ] Public verification page accessible without authentication and without motion.
- [ ] No time-limited UI except token expiry, which is displayed as text with sufficient warning.

## Known gaps

- No formal WCAG audit with assistive-technology users.
- Chart alternatives are basic; production needs tested data-table equivalents.
- Language/localization is English-only.
- PDF/print certificate output is out of scope.
