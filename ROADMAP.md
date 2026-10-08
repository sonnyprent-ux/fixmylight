# Roadmap

The guiding rule for every channel: **one fault, one conversation, one reminder per working day at most,
stop the moment it's fixed.** New channels add reach, not volume.

## v0.1 (this release)
- [x] Web form and CLI reporting
- [x] Initial email + threaded daily follow-ups until fixed
- [x] Duplicate merging, caps, weekend skip, dry-run default
- [x] Optional AI polishing that cannot change facts
- [x] WCAG 2.2 AA interface, no-JS support
- [x] Hosted one-stop web app: Docker, one-click Render deploy, built-in daily scheduler
- [x] Fault page with call, post-on-X, WhatsApp share, copy text and "I see it too"
- [x] Installable on phones (web app manifest)

## v0.2: Close the loop automatically
- [ ] Read the reply inbox over IMAP; pull out the city's reference number and attach it to the fault
- [ ] Detect "resolved/closed" replies and ask the reporter to confirm before stopping
- [ ] "Is it still broken?" one-tap email/SMS to the reporter every few days
- [ ] Simple map of open faults (with a text table alternative)

## v0.3: Automated messages
- [ ] **WhatsApp / SMS to reporters** for status updates and "still broken?" checks
      (e.g. via Twilio or Clickatell; opt-in only, POPIA-compliant, STOP to unsubscribe)
- [x] Person-reviewed post to X tagging `@CityofJoburgZA` (done in v0.1)
- [ ] Automatic weekly public status post to X from a project account
      (once at report time, once weekly while open; never daily, to avoid looking like spam)
- [ ] Submit through official channels where an API or form exists, so faults enter the city's own system

## v0.4: Phone calls (handle with care)
Automated calls to a municipal call centre tie up lines that people with emergencies also use, so:
- [x] **Assisted calling:** one-tap call button with the reference to quote (done in v0.1)
- [ ] **AI voice calls only with the city's agreement**, at most once per fault per week, identifying
      themselves as automated in the first sentence, and only for faults past an agreed age
- [ ] Never call emergency numbers (10111, 112) or JMPD lines

## Later
- [ ] Other metros (Tshwane, Ekurhuleni, Cape Town) via a per-city config of recipients
- [ ] isiZulu, Sesotho, Afrikaans and other language versions of the form
- [ ] Open data export of fault durations for councillors and journalists
- [ ] Docker image and one-click deploy
