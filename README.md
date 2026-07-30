# OWN — Instagram Daily Performance Report

Sends one HTML email every morning at **08:45 IST** covering [@onlywhatsneeded](https://instagram.com/onlywhatsneeded):
follower movement, latest-post performance vs. the rolling median, comment
sentiment and topic mining, objections/questions surfaced from the community, a
competitor benchmark, and a Reddit mentions sweep.

New owner? Read **[docs/HANDOVER.md](docs/HANDOVER.md)** first — it is the
inventory and the cutover runbook, and it lists the two things that will
silently break if you skip them.

## Layout

```
own_scorer/
  scraper.py            the whole report: scrape → analyse → render → send
  history_own.json      rolling post history (committed by the workflow)
  followers_own.json    daily follower snapshots
  snapshots_own.json    per-post metric snapshots for trend deltas
  competitors_own.json  cached weekly competitor pull
shared_reddit.py        Reddit fetch helpers (Apify-backed)
.github/workflows/
  own-daily.yml         the scheduled job
secrets/app.env.example template for local runs
```

## Run it locally

```bash
pip install -r requirements.txt
cp secrets/app.env.example secrets/app.env    # fill in the 5 required values
cd own_scorer
TEST_MODE=true python scraper.py              # sends only to you
```

`TEST_MODE=true` sends to `TEST_EMAIL` (defaults to `GMAIL_USER`) instead of the
full distribution list. Use it for every change. A normal run emails 10 people
including the founder.

## Required secrets

| Name | Used for |
|---|---|
| `APIFY_TOKEN` | Instagram + Reddit scraping |
| `GEMINI_API_KEY` | reel/carousel + comment analysis |
| `GROQ_API_KEY` | text analysis, comment classification |
| `GMAIL_USER` | SMTP sender — this address is the visible "From" |
| `GMAIL_APP_PASS` | 16-char Google app password (needs 2FA on the account) |

Optional: `FP_HISTORY_URL`, `EMAIL_TO_OVERRIDE`, `TEST_MODE`, `TEST_EMAIL`.

## Scheduling — read this before you assume it works

The workflow has **no native GitHub cron**. GitHub's scheduler silently dropped
runs in June 2026, so triggering moved to an external scheduler (cron-job.org)
that POSTs to the `workflow_dispatch` endpoint at 08:45 IST.

That means: **fork or transfer this repo and nothing runs at all** until you
create your own scheduler job pointing at it. Nothing warns you. See
HANDOVER.md step 4.

## Standing rules

- **Never name, tag, show, or compare against another brand** in anything the
  report suggests OWN should post. Advice stays generic ("most protein
  powders", "the category"). Naming a rival reads as FoodPharmer trashing
  competitors to promote his own brand. This is baked into the Gemini prompts
  and is a hard blocker, not a preference.
- Don't restructure the email HTML unless asked — the Gmail renderer is brittle
  and Gmail clips messages over 102KB.
- History upserts carry forward sentiment/topic/video scores. Don't regress that.
- Posts co-authored with @foodpharmer are excluded from OWN's median baseline —
  their borrowed reach made solo posts read as underperforming.
