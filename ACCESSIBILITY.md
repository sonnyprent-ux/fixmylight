# Accessibility statement

FixMyLight aims to meet **WCAG 2.2 level AA**. Anyone should be able to report a broken traffic light,
including people who use screen readers, keyboard only, voice control, magnification, or older phones
on slow data.

## What we do
- **Semantic HTML**: landmarks (`header`, `nav`, `main`, `footer`), one `h1` per page, real `<button>`s,
  `<fieldset>`/`<legend>` for the radio group, table headers with `scope` and a caption.
- **Skip link** to the main content.
- **Every input has a visible label**, plus a hint linked with `aria-describedby`.
- **Errors**: a summary at the top with `role="alert"` that receives focus and links to each field;
  each field shows its own message, is marked `aria-invalid`, and the page title starts with "Error:".
- **No CAPTCHA**: bots are filtered with a hidden honeypot field instead.
- **Keyboard**: everything reachable and operable; strong visible focus ring (yellow with dark halo).
- **Touch targets** at least 44 × 44 px; large radio buttons.
- **Contrast**: text and controls meet 4.5:1 in both light and dark themes; status is never shown by
  colour alone (pills always contain the word).
- **Reflow**: single column, works at 320 px wide and 400 % zoom with no horizontal scrolling;
  wide tables scroll inside their own focusable region.
- **Progressive enhancement**: works fully with JavaScript off. "Add my current location" only appears
  when the browser supports it, announces results through a polite live region, and is optional.
- **Reduced motion** respected; no animations are required.
- **Plain language**, `lang="en-ZA"`.
- **Lightweight**: one small CSS file, no web fonts, no tracking, good on low data.

## Testing checklist for contributors
- [ ] Keyboard-only pass (Tab, Shift+Tab, Space, Enter)
- [ ] NVDA + Firefox or VoiceOver + Safari: submit with errors, then correct them
- [ ] 400 % zoom at 1280 px wide, and 320 px wide
- [ ] axe DevTools or Lighthouse: no violations
- [ ] Dark mode check

## Report a barrier
Open an issue with the label `accessibility`. We treat these as bugs, not feature requests.
