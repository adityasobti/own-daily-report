"""Preflight — validate every credential before the real run.

The daily report takes 35-48 minutes. Discovering a bad key at minute 40 is the
expensive way to find out. This checks all five secrets in about 30 seconds and
says exactly which one is wrong and how to fix it.

Run it from the Actions tab (Preflight Check) or locally:

    cd own_scorer && python ../preflight.py

Exit code 0 = every check passed, the real run will work.
"""
import json
import os
import smtplib
import ssl
import sys
import urllib.error
import urllib.request

# Groq sits behind Cloudflare, which blocks urllib's default User-Agent with a
# 403 that looks exactly like an auth failure. Always send a browser UA.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

results = []


def record(name, ok, detail, fix=""):
    results.append((name, ok, detail, fix))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")
    if not ok and fix:
        print(f"        fix: {fix}")


def get(url, headers=None, data=None, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})},
                                 data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


print("\nPreflight — checking every credential the daily report needs.\n")

# ── 1. Are all five even present? ────────────────────────────────────────────
print("[1/6] Secrets present")
required = ["APIFY_TOKEN", "GEMINI_API_KEY", "GROQ_API_KEY", "GMAIL_USER", "GMAIL_APP_PASS"]
missing = [k for k in required if not os.getenv(k, "").strip()]
record("all five set", not missing,
       "all present" if not missing else f"missing: {', '.join(missing)}",
       "Settings -> Secrets and variables -> Actions. Names must match exactly.")
if missing:
    print("\nStopping — can't check credentials that aren't set.\n")
    sys.exit(1)

# ── 2. Apify ─────────────────────────────────────────────────────────────────
print("\n[2/6] Apify")
tok = os.environ["APIFY_TOKEN"].strip()
try:
    d = get(f"https://api.apify.com/v2/users/me?token={tok}")["data"]
    plan = d.get("plan") or {}
    record("token valid", True, f"account '{d.get('username')}', plan {plan.get('id')}")
    limit = plan.get("maxMonthlyUsageUsd")
    if limit:
        print(f"        monthly cap ${limit} — if this is exhausted the scrape returns nothing")
except urllib.error.HTTPError as e:
    record("token valid", False, f"HTTP {e.code}",
           "Regenerate at console.apify.com -> Settings -> Integrations.")
except Exception as e:
    record("token valid", False, f"{type(e).__name__}")

# ── 3. Gemini ────────────────────────────────────────────────────────────────
print("\n[3/6] Gemini")
try:
    d = get(f"https://generativelanguage.googleapis.com/v1beta/models"
            f"?key={os.environ['GEMINI_API_KEY'].strip()}")
    names = [m.get("name", "") for m in d.get("models", [])]
    has_pro = any("2.5-pro" in n or "2.0" in n or "1.5-pro" in n for n in names)
    record("key valid", True, f"{len(names)} models visible")
    record("a usable model present", has_pro,
           "yes" if has_pro else "no recent Gemini model visible to this key",
           "Check the key's project has the Generative Language API enabled.")
except urllib.error.HTTPError as e:
    record("key valid", False, f"HTTP {e.code}",
           "Generate a new key at aistudio.google.com/apikey.")
except Exception as e:
    record("key valid", False, f"{type(e).__name__}")

# ── 4. Groq ──────────────────────────────────────────────────────────────────
print("\n[4/6] Groq")
try:
    body = json.dumps({"model": "llama-3.3-70b-versatile",
                       "messages": [{"role": "user", "content": "reply with: ok"}],
                       "max_tokens": 5}).encode()
    d = get("https://api.groq.com/openai/v1/chat/completions",
            {"Authorization": f"Bearer {os.environ['GROQ_API_KEY'].strip()}",
             "Content-Type": "application/json"}, body)
    record("key valid + model reachable", True,
           f"completion returned from {d.get('model')}")
except urllib.error.HTTPError as e:
    hint = ("Generate a new key at console.groq.com/keys."
            if e.code == 401 else
            "403 here is usually Cloudflare, not the key — retry once.")
    record("key valid + model reachable", False, f"HTTP {e.code}", hint)
except Exception as e:
    record("key valid + model reachable", False, f"{type(e).__name__}")

# ── 5. Gmail SMTP — the most common thing to get wrong ───────────────────────
print("\n[5/6] Gmail SMTP")
user = os.environ["GMAIL_USER"].strip()
pw   = os.environ["GMAIL_APP_PASS"].strip()

compact = pw.replace(" ", "")
if len(compact) != 16:
    record("app password shape", False,
           f"{len(compact)} characters, expected 16",
           "This must be a Google APP PASSWORD, not your account password. "
           "Create one at myaccount.google.com/apppasswords (needs 2FA).")
else:
    record("app password shape", True, "16 characters")

if "@" not in user:
    record("sender address", False, f"'{user}' is not an email address", "")
else:
    record("sender address", True, user)

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30,
                          context=ssl.create_default_context()) as s:
        s.login(user, compact)
    record("SMTP login", True, "authenticated, report can send")
except smtplib.SMTPAuthenticationError:
    record("SMTP login", False, "rejected by Google",
           "Wrong app password, or 2FA is off on this account, or you used the "
           "account password. Regenerate at myaccount.google.com/apppasswords.")
except Exception as e:
    record("SMTP login", False, f"{type(e).__name__}: {e}")

# ── 6. The two scrapes the run depends on ────────────────────────────────────
print("\n[6/6] Instagram scrapes (this is the slow one, ~1-2 min)")
def scrape(handle):
    body = json.dumps({"directUrls": [f"https://www.instagram.com/{handle}/"],
                       "resultsType": "details", "resultsLimit": 1}).encode()
    d = get(f"https://api.apify.com/v2/acts/apify~instagram-scraper/run-sync-get-dataset-items"
            f"?token={tok}&timeout=180",
            {"Content-Type": "application/json"}, body, timeout=200)
    return d[0] if d else {}

for handle, why in (("onlywhatsneeded", "the report's subject"),
                    ("foodpharmer", "FoodPharmer-effect box + collab detection")):
    try:
        p = scrape(handle)
        followers = p.get("followersCount")
        posts = p.get("latestPosts") or []
        ok = bool(followers and posts)
        record(f"@{handle}", ok,
               f"{followers:,} followers, {len(posts)} posts" if ok
               else "scrape returned no usable data",
               "" if ok else f"Needed for {why}. Retry — Instagram blocks intermittently.")
    except Exception as e:
        record(f"@{handle}", False, f"{type(e).__name__}",
               f"Needed for {why}.")

# ── Verdict ──────────────────────────────────────────────────────────────────
failed = [r for r in results if not r[1]]
print("\n" + "=" * 62)
if failed:
    print(f"NOT READY — {len(failed)} check(s) failed:\n")
    for name, _, detail, fix in failed:
        print(f"  - {name}: {detail}")
        if fix:
            print(f"      {fix}")
    print("\nFix these, then run Preflight again. Don't schedule until it's green.")
else:
    print("READY — every credential works. The real run will send.")
    print("\nNext: Actions -> OWN Daily Report -> Run workflow, with")
    print("  recipient_override = your email")
    print("  skip_history_commit = true")
print("=" * 62 + "\n")

sys.exit(1 if failed else 0)
