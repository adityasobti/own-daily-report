# OWN Daily Report — Handover

**From:** Dev Narsinghani (left the org July 2026)
**To:** Aditya Sobti (`aditya.sobti@onlywhatsneeded.in`)
**Written:** 2026-07-30
**Status of the pipeline right now:** LIVE and green. Last successful run
2026-07-30 03:15 UTC (08:45 IST), delivered to 10 recipients.

This document is the inventory and the cutover runbook. Work it top to bottom.
Tick the boxes as you go — a half-finished cutover fails silently, and section
6 explains exactly how.

---

## 1. What this is

One HTML email, every morning at **08:45 IST**, about
[@onlywhatsneeded](https://instagram.com/onlywhatsneeded):

- follower movement vs. 7-day and 30-day trend
- latest post vs. the rolling median (likes, comments, engagement rate)
- comment sentiment + topic mining
- objections and questions surfaced from the community
- competitor benchmark against @thewholetruthfoods and @be.superyou
- a "FoodPharmer effect" box when a @foodpharmer post drove the day's movement
- Reddit mentions sweep
- Monday: a weekly rollup section

**Current recipients (10).** These are hardcoded in
`own_scorer/scraper.py` under `_EMAIL_TO_ALL`:

```
akhil.menon@onlywhatsneeded.in     dristi.patni@onlywhatsneeded.in
aditya.sobti@onlywhatsneeded.in    pavitra.shetty@onlywhatsneeded.in
dhyanesh@mosaicwellness.in         dev.narsinghani@gmail.com   ← remove at step 7
foodpharmer@gmail.com              aarfa.shaikh@gmail.com
samvida.patel@nyu.edu              bharath@onlywhatsneeded.in
```

Revant reads this on a phone. Don't restructure the HTML casually.

---

## 2. Where it lives today, and what changes

Until now the OWN report shared one repo with the FoodPharmer daily report, the
foodpharmer.health weekly analytics digest, and a corpus extractor. That repo is
`devnarsinghani22/-foodpharmer-reports` — **Dev's personal GitHub account, and
it is public.**

This repo is the OWN report carved out on its own, so nothing you own depends on
Dev's personal account staying alive. The FoodPharmer report, the analytics
digest and the corpus extractor stay where they are and are not yours.

**One deliberate dependency survives the split.** The report's "FoodPharmer
effect" box and its collab detection both need @foodpharmer's post history. That
used to be a file on disk in the shared repo. It is now fetched over HTTPS from
the FoodPharmer repo's public copy:

```
https://raw.githubusercontent.com/devnarsinghani22/-foodpharmer-reports/main/instagram_scorer/history_ig.json
```

Verified working 2026-07-30 (HTTP 200, 47 posts, 5-minute CDN cache — fresh well
inside the 30-minute gap between the 08:15 FP run and this 08:45 one).

If that repo is ever renamed, moved, or made private, set the `FP_HISTORY_URL`
repo variable to the new location. If it disappears entirely, set it to `off`.
Either way **the report still sends** — it just drops the FoodPharmer-effect box
and falls back to owner-based collab detection. It does not crash.

---

## 3. Inventory — every account and credential

| # | Asset | Owner today | What has to happen | Who does it |
|---|---|---|---|---|
| 1 | Code repo | `devnarsinghani22` (personal, **public**) | Push this repo to Aditya's GitHub. See step 1. | Dev + Aditya |
| 2 | `APIFY_TOKEN` | Apify user `resolute_mountainash`, login `ai.projects@onlywhatsneeded.in`, STARTER plan, $200/mo cap | Company-owned already. **But the login mailbox is Dev's old company address** — get IT to keep it alive or change the Apify account email before it's deactivated, or you lose password reset. | Aditya + IT |
| 3 | `GROQ_API_KEY` | Valid, but the **same key is reused in 5 of Dev's repos**, including his personal `life-ops` and `reddit_digest` | **Issue a fresh key** on an OWN-owned Groq account. Don't inherit this one — the day Dev rotates it, your report breaks with no warning. | Aditya |
| 4 | `GEMINI_API_KEY` | Valid; bound to a Google Cloud / AI Studio project whose owner the API does not expose | Confirm which Google account holds it. If it's Dev's personal, **issue a fresh key**. | Aditya |
| 5 | `GMAIL_USER` / `GMAIL_APP_PASS` | `dev.narsinghani@gmail.com` + 16-char app password | Becomes Aditya's address + his own app password. This is the visible "From" on the email. | Aditya |
| 6 | Scheduler | cron-job.org job **7850492** on **Dev's personal cron-job.org account**, authenticating with a fine-grained GitHub PAT on Dev's account | Aditya creates his own cron-job.org job + his own PAT against the new repo. **Nothing runs until this exists.** | Aditya |
| 7 | Recipient list | Hardcoded in `scraper.py` | Remove Dev at step 7. | Aditya |
| 8 | `YOUTUBE_API_KEY` | Dev | Not used by the OWN report. Ignore. | — |

Secrets 2–5 are the five the workflow needs. Nothing else.

---

## 4. Cutover runbook

### Step 1 — Create the repo
- [ ] Aditya sends Dev his GitHub username.
- [ ] Create **`<ADITYA_GH>/own-daily-report`**.
- [ ] **Make it private.** The current repo is public, which means the recipient
      list and internal brand prompts are world-readable today. Private is the
      right call.
      *Cost check:* this job runs 35–48 min/day ≈ **1,200 min/month** against the
      2,000 free private-repo Actions minutes. It fits, with ~40% headroom. If
      you later add jobs to the same account, watch that number.
- [ ] Dev pushes this prepared repo to it (`git push -u origin main`).

### Step 2 — Load the five secrets
Settings → Secrets and variables → Actions → New repository secret:
- [ ] `APIFY_TOKEN`
- [ ] `GROQ_API_KEY`  *(fresh key — see inventory #3)*
- [ ] `GEMINI_API_KEY`  *(fresh key if #4 turns out to be Dev's personal)*
- [ ] `GMAIL_USER` = Aditya's sending address
- [ ] `GMAIL_APP_PASS` = Aditya's 16-char app password

Google app passwords need 2FA on the account:
https://myaccount.google.com/apppasswords . It is **not** the account password.
Store all five in the team password manager — GitHub will not show them again.

### Step 3 — Test send before anything is scheduled
- [ ] Actions → *OWN Daily Report* → **Run workflow**, with:
      - `recipient_override` = `aditya.sobti@onlywhatsneeded.in`
      - `skip_history_commit` = **true**
- [ ] Email arrives, renders correctly, "From" is Aditya.
- [ ] In the run log, confirm `FP history: NN posts (fetched)`.
      If it says the fetch failed, the FoodPharmer-effect box is off — not fatal,
      but fix `FP_HISTORY_URL` before going live.

### Step 4 — Stand up the scheduler (the step that silently kills this)
- [ ] Aditya creates a fine-grained GitHub PAT on his account: repo-scoped to
      `own-daily-report`, permission **Actions: read and write**, long expiry.
      Calendar a reminder before it expires.
- [ ] Create a cron-job.org account (or any scheduler) and a daily job at
      **08:45 IST / 03:15 UTC**:
      ```
      POST https://api.github.com/repos/<ADITYA_GH>/own-daily-report/actions/workflows/own-daily.yml/dispatches
      Headers: Authorization: Bearer <PAT>
               Accept: application/vnd.github+json
      Body:    {"ref":"main"}
      ```
      Expect **HTTP 204** on success.
- [ ] Fire it once manually from the scheduler UI and confirm a run appears.
- [ ] Ask Dev to disable his job 7850492 on the same day you enable yours, so no
      double-send.

### Step 5 — Live for a week, both watching
- [ ] Dev stays on the recipient list and on his scheduler standby for 7 days.
- [ ] Confirm a green run each morning. First Monday, confirm the weekly rollup.

### Step 6 — Dev steps out
- [ ] Delete `dev.narsinghani@gmail.com` from `_EMAIL_TO_ALL` in
      `own_scorer/scraper.py` (the line is commented for you).
- [ ] Dev deletes cron-job.org job 7850492 and revokes his `CRONJOB_DISPATCH_PAT`.
- [ ] Dev revokes the Gmail app password used by the old pipeline.
- [ ] Change the Apify account email off `ai.projects@onlywhatsneeded.in`, or
      confirm with IT that the mailbox stays alive.
- [ ] Rotate the shared Groq key out of this repo if step 2 didn't already.

### Step 7 — Retire the old path
- [ ] In `devnarsinghani22/-foodpharmer-reports`, delete
      `.github/workflows/own-daily.yml` and the `own_scorer/` directory so no
      one can accidentally trigger a second OWN report.
- [ ] Leave `instagram_scorer/history_ig.json` in place — this repo reads it.

---

## 5. Verification checklist

Run through this once after step 4 and once after step 6.

- [ ] Manual `workflow_dispatch` completes green in ~35–48 min.
- [ ] Email lands, from Aditya, correct subject with 🟢/🟡/🔴.
- [ ] Follower numbers and the median comparison are populated, not zeros.
- [ ] Comment sentiment and topic chips render.
- [ ] Competitor benchmark table has rows for both competitors.
- [ ] Run log shows `FP history: NN posts (fetched)`.
- [ ] A scheduled (not manual) run fires the next morning at 08:45 IST.
- [ ] `own_scorer/history_own.json` gets a `[skip ci]` commit after each run.
- [ ] Monday: weekly rollup section present.

---

## 6. How this fails silently — read this twice

1. **No scheduler = no report, and no error.** There is no native GitHub cron in
   this workflow. GitHub's scheduler dropped runs in June 2026 and was
   deliberately abandoned. If you never create the cron-job.org job, the workflow
   simply never fires. No failure email, because nothing ran. **Check the Actions
   tab on day one and day two.**

2. **PAT expiry.** The scheduler authenticates with a fine-grained PAT. When it
   expires, cron-job.org starts getting 401s and the report stops. cron-job.org
   can email you on failure — turn that on.

3. **The history file must be committed.** Each run commits updated
   `history_own.json` / `followers_own.json` / `snapshots_own.json`. If the
   workflow loses `contents: write`, trend and median comparisons silently
   degrade to a single data point.

4. **Gmail clips emails over 102KB.** Adding sections without watching size makes
   the bottom of the report vanish in Gmail, with no error anywhere.

5. **Apify $200/month cap.** Shared with other scrapers on the same account.
   Blowing the cap means the morning scrape returns nothing and you get a red
   failure email. Check usage at the start of each month.

---

## 7. Tribal knowledge

- **Hard brand rule, non-negotiable:** the report must never suggest OWN name,
  tag, show, or compare itself against another brand. Advice stays generic
  ("most protein powders", "the category"). Naming a rival reads as FoodPharmer
  trashing competitors to promote his own brand. This is baked into the Gemini
  prompts. Don't loosen it.
- **Collab posts are excluded from the median on purpose.** Posts co-authored
  with @foodpharmer borrow his reach; leaving them in made OWN's solo posts look
  like they were underperforming. They're detected by cross-matching post IDs
  against FP's history (shortcodes are globally unique, so no false positives)
  and shown with a 🤝 banner instead.
- **Instagram's posts endpoint is blocked at Apify.** `resultsType:"posts"`
  returns error stubs ("Empty or private data"). The fix, already in the code, is
  to use the profile/`details` scrape, which embeds `latestPosts` with full data.
  Don't "fix" this back.
- **Posts with no timestamp are skipped deliberately.** They used to be parsed as
  `now()` and hoisted to "latest post", producing a phantom 0-likes entry.
- **Groq rate-limits on comment batches over ~200.** The code samples. Hinglish
  comments sometimes classify as neutral; known, accepted.
- **Don't restructure the email HTML unless asked.** The Gmail renderer is
  brittle and this has bitten before.
- **This report runs 30 minutes after the FoodPharmer one** so FP's history is
  already published when this one reads it. If you ever move the schedule
  earlier, the FoodPharmer-effect box goes stale.

---

## 8. Open items

- [ ] **Aditya's GitHub username** — blocks step 1.
- [ ] **Who owns the Gemini key's Google project?** Not resolvable from the API.
      Check Dev's AI Studio / Cloud console before trusting it.
- [ ] **Apify account email** is Dev's old company address. Highest-risk item on
      this page: it's the password-reset path for a $200/month company account.
- [ ] **Groq key is shared with Dev's personal projects.** Fresh key strongly
      recommended, not optional in spirit.
- [ ] **No alerting on a missed run.** Today, if the scheduler dies, the only
      signal is a human noticing no email. Worth adding a watchdog.
