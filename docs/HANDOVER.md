# OWN Daily Report — Handover

**From:** Dev Narsinghani (left the org July 2026)
**To:** Aditya Sobti (`aditya.sobti@onlywhatsneeded.in`)
**Written:** 2026-07-30
**Status right now:** LIVE and green, still running out of Dev's old repo. Last
successful run 2026-07-30 08:45 IST.

This is the inventory and the cutover runbook. Work it top to bottom. A
half-finished cutover fails silently — section 6 explains exactly how.

**As of 2026-07-30 this is the only report still running.** The FoodPharmer
daily report was retired the same day, and the foodpharmer.health weekly
analytics digest was already switched off. Nothing else survives.

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

**Recipients (9),** hardcoded in `own_scorer/scraper.py` under `_EMAIL_TO_ALL`:

```
akhil.menon@onlywhatsneeded.in     dristi.patni@onlywhatsneeded.in
aditya.sobti@onlywhatsneeded.in    pavitra.shetty@onlywhatsneeded.in
dhyanesh@mosaicwellness.in         aarfa.shaikh@gmail.com
foodpharmer@gmail.com              bharath@onlywhatsneeded.in
samvida.patel@nyu.edu
```

Dev was removed from this list on 2026-07-30 at his own instruction. He will not
see the report and cannot spot a bad send for you. **Watch the first week
yourself.**

Revant reads this on a phone. Don't restructure the HTML casually.

---

## 2. Where it lives today, and what changes

The OWN report used to share one repo with the FoodPharmer daily report, the
foodpharmer.health analytics digest, and a corpus extractor:
`devnarsinghani22/-foodpharmer-reports` — Dev's personal GitHub account.

This repo is that report carved out on its own, so nothing you operate depends
on Dev's account staying alive.

**It is fully decoupled.** The report needs @foodpharmer's recent posts for two
things: the FoodPharmer-effect box, and the collab cross-match that keeps FP
co-authored posts out of OWN's median baseline. That used to be a file read from
the FoodPharmer report's output. Since that report is retired and its file is
frozen forever, `load_fp_history()` now **scrapes @foodpharmer's grid directly**
— one extra Apify profile call per run.

Verified live 2026-07-30: 12 posts returned, every row carrying the id,
timestamp, caption and URL the two consumers need, cached so it costs one call
per run. Cross-checked against the old frozen file — same newest post.

This matters more than it looks. If an OWN×FP collab post goes undetected, its
borrowed reach inflates OWN's median and makes solo posts read as
underperforming. That's the exact bug the cross-match exists to prevent, and a
frozen file would have reintroduced it the first time Revant co-posted.

`FP_HISTORY_URL` remains as an optional override if a published history JSON
ever exists again. Set it to `off` to drop both features. Either way **the
report still sends** — it degrades, it does not crash.

---

## 3. Inventory — every account and credential

| # | Asset | Owner today | What has to happen | Who |
|---|---|---|---|---|
| 1 | Code repo | `devnarsinghani22` (personal, public) | Push this repo to Aditya's GitHub. Public is fine — Dev's call, Aditya is internal. | Dev + Aditya |
| 2 | `APIFY_TOKEN` | Apify user `resolute_mountainash`, login `ai.projects@onlywhatsneeded.in`, STARTER, $200/mo cap | **Leave as is** — company account, Aditya is internal. One caveat in section 8. | — |
| 3 | `GROQ_API_KEY` | Valid, but the **same key is reused in 5 of Dev's repos**, including his personal `life-ops` and `reddit_digest` | **Issue a fresh key** on an OWN-owned Groq account. This one is not cleared: the day Dev rotates it for a personal project, this report breaks with no warning. | Aditya |
| 4 | `GEMINI_API_KEY` | Valid; the owning Google project is not exposed by the API | Confirm which Google account holds it. If personal to Dev, issue a fresh key. | Aditya |
| 5 | `GMAIL_USER` / `GMAIL_APP_PASS` | `dev.narsinghani@gmail.com` + app password | Becomes Aditya's address + his own app password. This is the visible "From". | Aditya |
| 6 | Scheduler | cron-job.org job **7850492** on **Dev's personal cron-job.org account**, using a fine-grained GitHub PAT on Dev's account | Aditya creates his own job + PAT against the new repo. **Nothing runs until this exists.** | Aditya |

Secrets 2–5 are the five the workflow needs. Nothing else.

---

## 4. Cutover runbook

### Step 1 — Create the repo
- [ ] Aditya sends Dev his GitHub username.
- [ ] Create **`<ADITYA_GH>/own-daily-report`** (public is fine).
- [ ] Dev pushes this prepared repo to it (`git push -u origin main`).

### Step 2 — Load the five secrets
Settings → Secrets and variables → Actions → New repository secret:
- [ ] `APIFY_TOKEN`
- [ ] `GROQ_API_KEY` *(fresh key — inventory #3)*
- [ ] `GEMINI_API_KEY` *(fresh key if #4 turns out to be Dev's personal)*
- [ ] `GMAIL_USER` = Aditya's sending address
- [ ] `GMAIL_APP_PASS` = Aditya's 16-char app password

App passwords need 2FA: https://myaccount.google.com/apppasswords . It is **not**
the account password. Store all five in the team password manager — GitHub will
never show them again.

Leave `FP_HISTORY_URL` unset. That is the correct production state.

### Step 3 — Test send before anything is scheduled
- [ ] Actions → *OWN Daily Report* → **Run workflow**:
      - `recipient_override` = `aditya.sobti@onlywhatsneeded.in`
      - `skip_history_commit` = **true**
- [ ] Email arrives, renders correctly, "From" is Aditya.
- [ ] Log shows `FP history: NN posts (live @foodpharmer scrape)`.

### Step 4 — Stand up the scheduler (the step that silently kills this)
- [ ] Aditya creates a fine-grained GitHub PAT: scoped to `own-daily-report`,
      permission **Actions: read and write**, long expiry. Calendar the expiry.
- [ ] cron-job.org (or any scheduler), daily at **08:45 IST / 03:15 UTC**:
      ```
      POST https://api.github.com/repos/<ADITYA_GH>/own-daily-report/actions/workflows/own-daily.yml/dispatches
      Headers: Authorization: Bearer <PAT>
               Accept: application/vnd.github+json
      Body:    {"ref":"main"}
      ```
      Expect **HTTP 204**.
- [ ] Turn on cron-job.org's failure notifications.
- [ ] Fire once manually; confirm a run appears in Actions.
- [ ] Dev disables job 7850492 the same day, so there's no double-send.

### Step 5 — Live for a week
- [ ] Confirm a green run each morning in the Actions tab.
- [ ] First Monday: confirm the weekly rollup renders.
- [ ] Dev keeps job 7850492 disabled-but-not-deleted for those 7 days as a
      rollback path.

### Step 6 — Close out Dev's side
- [ ] Dev deletes cron-job.org job 7850492 and revokes its PAT.
- [ ] Dev revokes the Gmail app password the old pipeline used.
- [ ] Rotate the Groq key out if step 2 didn't already.

### Step 7 — Retire the old path
- [ ] In `devnarsinghani22/-foodpharmer-reports`, delete `own-daily.yml` and
      `own_scorer/` so nobody can trigger a second OWN report.
- [ ] The rest of that repo is already dead and can go whenever Dev wants. This
      repo no longer reads anything from it.

---

## 5. Verification checklist

Run once after step 4 and once after step 6.

- [ ] Manual `workflow_dispatch` completes green in ~35–48 min.
- [ ] Email lands, from Aditya, subject carries 🟢/🟡/🔴.
- [ ] Follower numbers and median comparison populated, not zeros.
- [ ] Comment sentiment and topic chips render.
- [ ] Competitor table has rows for both competitors.
- [ ] Log shows `FP history: NN posts (live @foodpharmer scrape)`.
- [ ] A scheduled (not manual) run fires next morning at 08:45 IST.
- [ ] `history_own.json` gets a `[skip ci]` commit after each run.
- [ ] Monday: weekly rollup present.

---

## 6. How this fails silently — read twice

1. **No scheduler = no report, and no error.** There is no native GitHub cron
   here. GitHub's scheduler dropped runs in June 2026 and was deliberately
   abandoned. If you never create the cron-job.org job, the workflow simply never
   fires, and nothing warns you because nothing ran. **Check the Actions tab on
   day one and day two.**

2. **PAT expiry.** The scheduler authenticates with a fine-grained PAT. When it
   expires cron-job.org starts getting 401s and the report stops. Turn on
   cron-job.org failure notifications.

3. **Nobody is watching but you.** Dev is off the recipient list and out of the
   company. A silent stop now has no second pair of eyes behind it.

4. **The history file must be committed.** Each run commits `history_own.json`,
   `followers_own.json`, `snapshots_own.json`. Lose `contents: write` and trend
   and median comparisons silently degrade to a single data point.

5. **Gmail clips emails over 102KB.** Add sections without watching size and the
   bottom of the report vanishes in Gmail, with no error anywhere.

6. **Apify $200/month cap.** Shared with whatever else runs on that account.
   Blow the cap and the morning scrape returns nothing. Check usage monthly.

---

## 7. Tribal knowledge

- **Hard brand rule, non-negotiable:** the report must never suggest OWN name,
  tag, show, or compare itself against another brand. Advice stays generic
  ("most protein powders", "the category"). Naming a rival reads as FoodPharmer
  trashing competitors to promote his own brand. Baked into the Gemini prompts.
  Don't loosen it.
- **Collab posts are excluded from the median on purpose.** Posts co-authored
  with @foodpharmer borrow his reach; including them made OWN's solo posts look
  like they were underperforming. Detected by cross-matching post IDs against
  FP's grid (shortcodes are globally unique, so no false positives) and shown
  with a 🤝 banner.
- **Instagram's posts endpoint is blocked at Apify.** `resultsType:"posts"`
  returns error stubs ("Empty or private data"). The fix, already in the code, is
  the profile/`details` scrape, which embeds `latestPosts` with full data. Both
  the OWN scrape and the @foodpharmer scrape rely on this. Don't "fix" it back.
- **Posts with no timestamp are skipped deliberately.** They used to parse as
  `now()` and hoist to "latest post", producing a phantom 0-likes entry.
- **Groq rate-limits on comment batches over ~200.** The code samples. Hinglish
  comments sometimes classify neutral; known and accepted.
- **Don't restructure the email HTML unless asked.** The Gmail renderer is
  brittle and this has bitten before.

---

## 8. Open items

- [ ] **Aditya's GitHub username** — blocks step 1.
- [ ] **Groq key is shared with Dev's personal projects.** Fresh key strongly
      recommended. Not optional in spirit.
- [ ] **Who owns the Gemini key's Google project?** Not resolvable from the API.
      Check Dev's AI Studio / Cloud console before trusting it.
- [ ] **Apify login is `ai.projects@onlywhatsneeded.in`**, Dev's old company
      mailbox. Staying as is, but that address is the password-reset path for a
      $200/month company account. If IT ever deactivates it, recovery is gone —
      an IT ticket, not a handover blocker.
- [ ] **No alerting on a missed run.** If the scheduler dies, the only signal is
      a human noticing no email. Worth adding a watchdog.
