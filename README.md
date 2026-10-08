# 🚦 FixMyLight

**Report a broken traffic light once. FixMyLight emails the Johannesburg Roads Agency for you,
then sends one polite reminder every working day until it's fixed.**

**One link, nothing to install.** People open the site on their phone, report in about 30 seconds,
and get one page where they can also call the city, post on X, share on WhatsApp, or add "I see it too".
It can be added to the home screen like an app.

Open source (MIT), built to WCAG 2.2 AA, and works without JavaScript.

---

## What it does

1. **You report** a broken light on a simple web form (or from the terminal): the intersection,
   what's wrong, and optionally your GPS location.
2. **It emails the city** a clear, factual report and gives you a private status page.
3. **Every working day** a scheduled job sends a follow-up **in the same email thread**, quoting
   how many days the light has been out and how many people have reported it.
4. **It stops** the moment anyone marks the light as fixed, or after a cap (30 by default),
   at which point the fault is flagged *escalated* so a person can take it to the ward councillor.

### Built to be a good citizen, not a spam bot

The goal is to get lights fixed, and inboxes that are flooded get filtered. So by design:

| Guardrail | Default |
|---|---|
| One email thread per fault, never one per reporter | Duplicates within 75 m or with the same intersection name are merged; the reminder says "N people affected" instead |
| At most one reminder per fault per working day | `FIXMYLIGHT_FOLLOWUP_HOURS=24`, weekends skipped |
| Hard cap on reminders | `FIXMYLIGHT_MAX_FOLLOWUPS=30`, then *escalated* for a human |
| Stops on fix | Anyone with the private link can mark it fixed |
| Quotes the city's reference number | Paste it in once; every later subject line includes it |
| Test mode on by default | Nothing leaves your machine until `FIXMYLIGHT_DRY_RUN=false` |
| AI can only rephrase | Facts come from the database; if the AI output drops a fact, the plain template is used |

## Who to email (verify before going live!)

In the City of Johannesburg, traffic signals are maintained by the **Johannesburg Roads Agency (JRA)**.
Commonly published contacts at the time of writing:

- Email: `hotline@jra.org.za` (the default in `.env.example`)
- Joburg Connect call centre: **0860 562 874**
- Some intersections (often on provincial routes) belong to the **Gauteng Department of Roads and
  Transport** instead; a power failure at the signal may be **City Power** or **Eskom**.

Contacts change, so phone the call centre or check the JRA website before you switch off test mode.
Add your **ward councillor** in `FIXMYLIGHT_CC`; councillors can escalate in ways the public can't.

> **About `@CityofJoburgZA`:** that is the City's X (Twitter) account, not an email address.
> Posting to X is on the roadmap (see below).

## Put it online (the one-stop shop)

You host it once; everyone else just uses the link.

### Option A: Render (easiest)
1. Push this folder to a GitHub repository.
2. Open `https://render.com/deploy?repo=<your repo URL>`. Render reads `render.yaml` and sets everything up.
3. Fill in the blanks it asks for: SMTP details, `FIXMYLIGHT_FROM`, `FIXMYLIGHT_BASE_URL` (your site's address).
4. Send a test report, check the email log on its status page, then set `FIXMYLIGHT_DRY_RUN=false`.

`render.yaml` uses a small paid always-on instance with a 1 GB disk. Render's free services go to sleep
when idle and lose local files, which would wipe reports and skip the daily follow-ups.

### Option B: any server with Docker
```bash
docker build -t fixmylight .
docker run -d --name fixmylight -p 80:8000 --env-file .env -v fixmylight-data:/data fixmylight
```
Put it behind HTTPS (Caddy, Cloudflare, or your host's load balancer). Fly.io, Railway, a VPS or a
Raspberry Pi all work; the only requirements are an always-on process and a persistent `/data` folder.

The hosted app runs the daily follow-ups itself (`FIXMYLIGHT_SCHEDULER=true`, at `FIXMYLIGHT_RUN_AT`,
Johannesburg time), so there is no separate cron job to set up.

### What people see
| Page | What it does |
|---|---|
| **Report** (`/`) | Short form, optional "Add my current location", list of recently reported lights |
| **Fault page** (`/fault/FML-…`) | Status, people affected, every email sent, and buttons to **call Joburg Connect**, **post on X tagging @CityofJoburgZA**, **share on WhatsApp**, **copy the text**, or say **"I see this broken light too"** |
| **All faults** (`/faults`) | Open faults first |
| **How it works** (`/about`) | Plain-language explanation and privacy note |

The call, X and WhatsApp buttons open the person's own phone or app with the text filled in. They
review it and send it themselves, so the city's channels never receive bot traffic.

## Run it on your own computer

```bash
git clone https://github.com/<you>/fixmylight.git && cd fixmylight
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # add ,ai for optional AI polishing
cp .env.example .env             # then edit it
set -a && source .env && set +a

python -m fixmylight serve       # open http://127.0.0.1:5000
python -m fixmylight followup    # what the daily job runs
pytest                           # 10 tests
```

### Terminal-only use (no web server)

```bash
python -m fixmylight report "Witkoppen Rd and Maxwell Dr" --suburb Fourways --type off
python -m fixmylight list
python -m fixmylight ref FML-1A2B3C JRA-4471023     # store the city's reference
python -m fixmylight fixed FML-1A2B3C               # stop reminders
```

### Schedule the daily follow-up (only if not using the built-in scheduler)

Run it once a day, early on a weekday, so it lands before the morning shift starts.

**cron** (Linux/macOS), 07:10 SAST Monday–Friday:

```cron
CRON_TZ=Africa/Johannesburg
10 7 * * 1-5  cd /srv/fixmylight && set -a && . ./.env && set +a && .venv/bin/python -m fixmylight followup >> followup.log 2>&1
```

**Windows Task Scheduler:** create a daily task that runs
`C:\fixmylight\.venv\Scripts\python.exe -m fixmylight followup` with "Start in" set to the project folder.

The job is safe to run more than once a day: it only sends to faults that are due.

### Sending email

Any SMTP account works (Gmail with an app password, Outlook, Zoho, Mailgun, Amazon SES, etc.).
For best deliverability use your own domain with SPF and DKIM set up, and put a real person's
address in `FIXMYLIGHT_REPLY_TO` so the city can reply with a reference number.

## Accessibility

See [ACCESSIBILITY.md](ACCESSIBILITY.md). Highlights: semantic HTML, labelled fields with hints,
GOV.UK-style error summary that receives focus, `aria-invalid` and linked error messages, 44 px touch
targets, visible focus rings, AA contrast in light and dark mode, respects reduced motion, zoom to 400 %
without horizontal scrolling, and every feature works with JavaScript off (location is an optional extra).

## Project layout

```
fixmylight/
  app.py        web form, status page, list of faults
  cli.py        command line (serve, followup, report, list, ref, fixed, pause, reopen)
  followup.py   the daily job and its guardrails
  compose.py    email wording (templates + optional AI polishing)
  mailer.py     SMTP sending with threading headers
  db.py         SQLite storage and duplicate detection
  scheduler.py  built-in daily run for the hosted app
  channels.py   call / X / WhatsApp links for the fault page
  templates/    accessible HTML
  static/       one CSS file, no framework
tests/          pytest suite
```

## Roadmap

See [ROADMAP.md](ROADMAP.md): reading the city's replies automatically, SMS/WhatsApp updates to
reporters, assisted and automated phone calls, more cities, and more languages.

## Contributing

Issues and pull requests welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

MIT. See [LICENSE](LICENSE). Not affiliated with the City of Johannesburg or the JRA.
