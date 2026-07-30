# Setup — OWN Daily Report

Aditya: this is the OWN daily Instagram report, now yours.

**Nothing runs on anyone's laptop.** It runs on GitHub's servers, on a schedule
GitHub keeps itself. Your machine can be off, asleep, or at the bottom of a lake
and the report still sends. There is no other service, no password to renew, and
nothing of Dev's left in the path.

The report is one HTML email at **08:45 IST** to 9 people including Revant:
follower movement, latest post vs. the rolling median, comment sentiment and
topic mining, community objections and questions, a competitor benchmark, and a
Reddit mentions sweep. Monday adds a weekly rollup.

Full detail lives in [HANDOVER.md](HANDOVER.md).

## Status: already done and running

Dev completed the setup on 2026-07-30. The repo is yours, the credentials are
loaded and verified, and the schedule is live on GitHub's own cron. **The report
sends every morning without anyone doing anything.**

So this document is reference, not a to-do list. Read Parts 4 and 6 — the
schedule and the failure modes — and keep the rest for when something breaks.

The one thing worth doing soon: tell the recipient list the report now comes
from your address (Part 7), so it doesn't get filed as spam.

---

## Part 1 — What's already done

- Repo transferred to `adityasobti/own-daily-report` ✓
- All five credentials loaded and verified ✓
- Sending as `sobti.aditya9@gmail.com` (your app password) ✓
- Schedule live on GitHub cron, 08:45 IST daily ✓
- Test send verified ✓

Two housekeeping items for whenever you get to them:

1. **Rotate the app password.** The one in use was passed through chat during
   handover. Revoke it at myaccount.google.com/apppasswords, create a fresh one,
   and update the `GMAIL_APP_PASS` secret (Part 3 shows where). It only controls
   sending mail as you, not account access, so this isn't urgent.

2. **Consider a work sending address.** The report currently goes to Revant and
   leadership from a personal Gmail. A company address is a better long-term
   home — if you ever move on, the report's identity doesn't move with you.

---

## Part 2 — The repo

**Already done and waiting for you.** Dev pushed the code to
`devnarsinghani22/own-daily-report` and transferred it to you on 2026-07-30.

1. Accept the transfer — check your GitHub notifications, or
   https://github.com/adityasobti (the invite expires, so do this first).
2. After accepting, the repo is `adityasobti/own-daily-report` and you own it
   outright. Full commit history comes with it.
3. **Repository secrets do NOT survive a transfer.** You add all five yourself
   in Part 3. This is by design — no key of Dev's ends up on your account.

## Part 3 — The five secrets

These live at **Settings → Secrets and variables → Actions**. GitHub will never
show them to you again after you save them, so put a copy in the team password
manager at the same time.

| Secret | Where it comes from |
|---|---|
| `APIFY_TOKEN` | Dev. Company Apify account, staying as is. |
| `GEMINI_API_KEY` | Dev — but check Part 6 first. |
| `GROQ_API_KEY` | **Generate a fresh one yourself** at https://console.groq.com — see Part 6. |
| `GMAIL_USER` | Your sending address from Part 1. |
| `GMAIL_APP_PASS` | Your 16-character app password from Part 1. |

Leave `FP_HISTORY_URL` unset. Unset is the correct production state.

## Part 4 — The schedule

**Nothing to set up. It's already running.**

The workflow schedules itself with GitHub's built-in cron at 03:15 UTC (08:45
IST), so there is no external service, no access token, and no account of Dev's
involved. Check Settings → Actions → General → *Allow all actions* is on, and
that's it.

Two things to know:

- **The email can be late.** GitHub's scheduler is best-effort and runs behind
  when the platform is busy, so the report may land anywhere from 08:45 to about
  09:15 IST. It's never early. If exact timing ever becomes important, an
  external scheduler hitting the manual-trigger endpoint is the precise option.

- **How to tell it stopped.** Every successful run pushes a commit called
  `chore: update own_scorer history [skip ci]`. If the repo has no new commit
  from a given morning, the report didn't run. That's the cheapest health check —
  glance at the commit list, not your inbox.

GitHub disables scheduled workflows in repos that go 60 days without commits.
This one commits daily, so that won't trigger — but if you ever pause the report
for a couple of months, re-enable the schedule when you come back.

## Part 5 — Prove it works before it goes live

### 5a. Preflight first — one minute, checks everything

Actions → **Preflight Check** → **Run workflow**.

It validates all five secrets and both Instagram scrapes in about a minute, and
tells you exactly which one is wrong and how to fix it. Green here means the
real run will work.

Do this before the real run. The real run takes 35–48 minutes, so finding a bad
key that way costs you most of an hour. Run Preflight as many times as you need
until it says READY.

### 5b. Then the real thing

1. Actions → *OWN Daily Report* → **Run workflow**, with:
   - `recipient_override` = your email
   - `skip_history_commit` = **true**
2. Wait 35–48 minutes. That duration is normal.
3. Check the email: renders correctly, "From" is you, follower numbers and the
   median comparison are populated rather than zeros, sentiment and topic chips
   render, the competitor table has rows.
4. In the run log, look for `FP history: NN posts (live @foodpharmer scrape)`.
5. Then watch for a week: a green run every morning, and on the first Monday,
   the weekly rollup section.

Both of these were run and passed on 2026-07-30 before handover. Re-run them any
time you change a credential or something looks off.

## Part 6 — Two keys worth replacing

- **Groq: generate your own.** The key Dev used is the same key sitting in
  several of his personal projects. The day he rotates it for one of those, your
  report breaks at 08:45 with no warning. Free key, two minutes, do it.
- **Gemini: check before you trust it.** Nobody could determine from the API
  which Google account owns the project behind Dev's key. If it turns out to be
  personal, generate your own at https://aistudio.google.com/apikey.

## Part 7 — Tell the recipients

The "From" address changes from Dev's to yours. Send the list a one-liner before
the first live run, or the report lands in spam folders and looks like phishing:

> From tomorrow the daily OWN Instagram report will come from me instead of Dev.
> Same report, same time. If it lands in spam, please mark it "not spam" so it
> keeps arriving.

Recipients: akhil.menon@, aditya.sobti@, dhyanesh@mosaicwellness.in,
foodpharmer@gmail.com, samvida.patel@nyu.edu, dristi.patni@, pavitra.shetty@,
aarfa.shaikh@gmail.com, bharath@.

---

## Things that will bite you

- **A missed morning is silent.** If GitHub's scheduler skips a run there is no
  error and no email, because nothing started. The tell is the commit list: every
  successful run pushes a `chore: update own_scorer history` commit, so a morning
  with no commit is a morning with no report. A crash, by contrast, does email
  you a red failure report — don't filter those.
- **Don't restructure the email HTML** unless asked. The Gmail renderer is
  brittle, and Gmail clips anything over 102KB — the bottom of the report just
  vanishes with no error.
- **The report must never name, tag, show, or compare OWN against another
  brand.** Advice stays generic: "most protein powders", "the category". Naming
  a rival reads as FoodPharmer trashing competitors to promote his own brand.
  It's baked into the AI prompts. Don't loosen it.
- **The Apify account has a $200/month cap** shared with other scrapers. Blow it
  and the morning scrape returns nothing. Glance at usage monthly.
- **Posts co-authored with @foodpharmer are excluded from OWN's median on
  purpose.** They borrow his reach and made OWN's solo posts look like they were
  underperforming.
- **Test with `TEST_MODE=true`** for any local change. A normal run emails nine
  people including the founder.

## If the report doesn't arrive one morning

You don't need the command line for any of this — it's all buttons on
github.com.

**First, work out which of the two things happened.** Go to the repo →
**Actions** tab → *OWN Daily Report* in the left sidebar.

**Case A — there's a run, and it's red.** It started and crashed. Click the run,
click the failed step, and read the last few lines; the error is usually a
credential. Run **Preflight Check** (Actions → Preflight Check → Run workflow) —
it takes a minute and names the broken secret and how to fix it.

**Case B — there's no run at all for that morning.** GitHub's scheduler skipped
it. Nothing is broken; it just didn't fire. Send it manually:

1. Actions → *OWN Daily Report* → **Run workflow** (button on the right)
2. Leave both boxes **empty**
3. Click the green **Run workflow**

That sends the real report to everyone, 35–48 minutes later. Leaving the boxes
empty is what makes it the real thing — filling in `recipient_override` sends
only to that address, which is how you test without emailing the team.

If it skips more than once in a fortnight, GitHub's scheduler isn't reliable
enough for this and you should drive it from an external scheduler instead.
HANDOVER.md section 3 explains that setup.

**Don't panic about one late morning.** GitHub's cron runs behind when the
platform is busy. Anything up to about 09:15 IST is normal.

## Who to ask

Nobody, structurally. Dev has left the company, is off the recipient list, and
as of 2026-07-30 has no access to this repo. He can answer a question as a
favour, but he cannot see the report, cannot see a failure, and cannot fix
anything from his side.

You are the only person watching this. That's the point of the handover — but it
does mean a silent stop stays silent until you notice. Glancing at the commit
list once a week is the cheapest habit that catches it.

## Two loose ends Dev flagged

1. **The Groq key is shared.** `GROQ_API_KEY` is the same key Dev uses in two of
   his personal projects. It works today. But if he ever rotates it there, this
   report breaks at 08:45 with no warning and no obvious cause. Generating your
   own at https://console.groq.com/keys and replacing the secret takes two
   minutes and removes the trap permanently. Worth doing before you forget this
   sentence exists.

2. **The Gemini key's owner is unknown.** Nothing in the API reveals which
   Google account holds the project behind it. If it turns out to be Dev's
   personal account, the same silent-breakage risk applies. Generate your own at
   https://aistudio.google.com/apikey if you want certainty.

Neither is urgent. Both are the kind of thing that bites eighteen months later
when nobody remembers why.
