# Setup — OWN Daily Report

Aditya: this is everything you need to take over the OWN daily Instagram report.
Work it top to bottom. Budget about an hour, plus a week of light watching.

The report is one HTML email at **08:45 IST** to 9 people including Revant:
follower movement, latest post vs. the rolling median, comment sentiment and
topic mining, community objections and questions, a competitor benchmark, and a
Reddit mentions sweep. Monday adds a weekly rollup.

Full detail lives in [HANDOVER.md](HANDOVER.md). This file is just your path to
a working handover.

---

## Part 1 — Three things to send Dev first

Nothing can start until Dev has these.

1. **Your GitHub username.**

2. **The address the report should send FROM,** plus a Google **app password**
   for it. This becomes the visible "From" on every report, so use a work
   address, not a personal one.
   - Enable 2FA on that Google account.
   - Go to https://myaccount.google.com/apppasswords
   - Create one named `own-daily-report`. You get a 16-character string.
   - That string is **not** your account password. Treat it like a password —
     anyone holding it can send mail as you.

3. **Confirm you can create a cron-job.org account** (free), or tell Dev which
   scheduler you'd rather use. You need something that can fire one HTTPS POST
   per day. See Part 4 for why this is not optional.

---

## Part 2 — The repo

1. Create a repo on your account called **`own-daily-report`**.
2. Add Dev as a collaborator with **Admin** access, temporarily.
3. Dev pushes the code and loads the secrets directly into GitHub, so the API
   keys never travel through chat or email.
4. Remove Dev's collaborator access once Part 5 verifies. Don't skip this.

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

## Part 4 — The scheduler, and why it is the whole ballgame

**This workflow has no built-in schedule.** GitHub's own cron silently dropped
runs in June 2026 and was deliberately abandoned. Triggering comes from an
external scheduler hitting GitHub's API.

So: **if you skip this step, nothing runs, ever, and nothing tells you.** There
is no error, because nothing started. This is the single most common way a
handover like this dies.

1. Create a **fine-grained personal access token** at
   https://github.com/settings/tokens?type=beta
   - Repository access: only `own-daily-report`
   - Permissions: **Actions → Read and write**
   - Set the longest expiry available, and put a calendar reminder two weeks
     before it expires. When this token dies, the report dies with it.

2. Create a cron-job.org account and a job:
   - **Schedule:** daily, 03:15 UTC (= 08:45 IST)
   - **Method:** POST
   - **URL:**
     ```
     https://api.github.com/repos/<your-username>/own-daily-report/actions/workflows/own-daily.yml/dispatches
     ```
   - **Headers:**
     ```
     Authorization: Bearer <your token>
     Accept: application/vnd.github+json
     ```
   - **Body:**
     ```json
     {"ref":"main"}
     ```
   - A successful call returns **HTTP 204** with an empty body. That's correct,
     not an error.

3. **Turn on cron-job.org's failure notifications.** This is your only warning
   system.

4. Hit "Test run" and confirm a run appears in the repo's Actions tab.

## Part 5 — Prove it works before it goes live

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

Dev keeps his old scheduler disabled but not deleted for that week, so there's a
rollback path.

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

## Who to ask

Dev wrote this and is reachable for questions during handover week, but he is
out of the company and off the recipient list — he will not see a bad send. From
cutover onward, you are the only person watching this.
