# Contributing

Thanks for helping get traffic lights fixed!

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```
`FIXMYLIGHT_DRY_RUN` defaults to `true`, so you can develop without sending real email.
**Never** run the follow-up job against real city addresses while testing.

## Ground rules
- **Accessibility is a requirement.** UI changes must pass the checklist in ACCESSIBILITY.md.
- **No spam.** Changes that increase how often a city is contacted need a clear reason and a guardrail.
- **Privacy (POPIA).** Don't collect reporters' names, emails or phone numbers unless a feature truly needs
  them, and then only with clear consent. Never include reporter personal details in emails to the city.
- **AI never invents facts.** Any AI-written text must be checked against data from the database.
- Keep dependencies minimal; the app should run on a cheap VPS or a Raspberry Pi.
- Add or update tests for behaviour changes.

## Good first issues
- Translations of `templates/*.html`
- IMAP reply reader (see ROADMAP v0.2)
- Per-city recipient config (Tshwane, Ekurhuleni, Cape Town)

By contributing you agree your work is released under the MIT licence.
Be kind; we follow the [Contributor Covenant](https://www.contributor-covenant.org/).
