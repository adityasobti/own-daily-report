"""Shared Reddit fetch helpers for instagram_scorer and own_scorer.

Reddit's anonymous JSON API returns 403 from GitHub Actions IPs, so we route
Reddit through the Apify actor `trudax/reddit-scraper-lite`. Reuses the
existing APIFY_TOKEN — no new accounts, no new secrets.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone

import requests

APIFY_BASE  = "https://api.apify.com/v2"
ACTOR_ID    = "trudax~reddit-scraper-lite"


def is_relevant(text: str, terms: list[str]) -> bool:
    t = text.lower()
    return any(term in t for term in terms)


def _parse_apify_ts(ts: str | None) -> datetime:
    """Parses '2023-06-09T05:23:15.000Z' → aware UTC datetime."""
    if not ts:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _run_apify_reddit(run_input: dict, label: str, apify_token: str,
                      max_wait_secs: int = 1200) -> list[dict]:
    """Mirrors the polling pattern in each scraper's run_apify_actor."""
    print(f"      -> [{ACTOR_ID}] {label} (poll budget {max_wait_secs}s)")
    r = requests.post(
        f"{APIFY_BASE}/acts/{ACTOR_ID}/runs",
        params={"token": apify_token},
        json=run_input, timeout=40,
    )
    r.raise_for_status()
    run_id = r.json()["data"]["id"]
    status = "RUNNING"
    s = None
    finished = False
    for attempt in range(max_wait_secs // 5):
        time.sleep(5)
        s = requests.get(
            f"{APIFY_BASE}/actor-runs/{run_id}",
            params={"token": apify_token}, timeout=20,
        )
        s.raise_for_status()
        status = s.json()["data"]["status"]
        if attempt % 6 == 0:
            print(f"         ... {status}")
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            finished = True
            break
    if not finished:
        # Stop the run so it doesn't keep burning compute (Apify bills by the
        # minute even after we stop polling). Best-effort — ignore abort errors.
        try:
            requests.post(f"{APIFY_BASE}/actor-runs/{run_id}/abort",
                          params={"token": apify_token}, timeout=20)
            print(f"         ↯ aborted run {run_id} (budget {max_wait_secs}s exhausted)")
        except Exception:
            pass
        raise RuntimeError(f"Reddit actor still {status} after {max_wait_secs}s — polling exhausted")
    if status != "SUCCEEDED" or s is None:
        raise RuntimeError(f"Reddit actor ended: {status}")
    dataset_id = s.json()["data"]["defaultDatasetId"]
    items = requests.get(
        f"{APIFY_BASE}/datasets/{dataset_id}/items",
        params={"token": apify_token, "limit": 1000}, timeout=40,
    ).json()
    print(f"         ✓ {len(items)} raw items")
    return items


def _community(item: dict) -> str:
    name = item.get("communityName") or item.get("parsedCommunityName") or ""
    return name.lstrip("r/").lstrip("/") if name else "—"


def fetch_reddit_posts(keywords: list[str], relevance_terms: list[str],
                       lookback_hours: int, apify_token: str | None = None,
                       max_wait_secs: int = 1200) -> list:
    """Single Apify run searching all keywords for posts. Returns shape compatible
    with the previous PRAW implementation (id/title/subreddit/score/comments/url/selftext/created)."""
    apify_token = apify_token or os.getenv("APIFY_TOKEN", "")
    if not apify_token:
        print("      ⚠ APIFY_TOKEN missing — Reddit posts skipped.")
        return []
    try:
        items = _run_apify_reddit(
            {
                "searches": list(keywords),
                "searchPosts": True,
                "searchComments": False,
                "sort": "new",
                "maxItems":     50 * len(keywords),
                "maxPostCount": 50 * len(keywords),
                "skipComments": True,
                "proxy": {"useApifyProxy": True},
            },
            "posts", apify_token, max_wait_secs=max_wait_secs,
        )
    except Exception as e:
        print(f"      ⚠ Reddit posts actor failed: {e}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    seen: set[str] = set()
    results: list[dict] = []
    for it in items:
        if it.get("dataType") != "post":
            continue
        pid = it.get("parsedId") or it.get("id") or ""
        if not pid or pid in seen:
            continue
        created = _parse_apify_ts(it.get("createdAt"))
        if created < cutoff:
            continue
        title    = it.get("title") or ""
        body     = it.get("body") or ""
        if not is_relevant(title + " " + body, relevance_terms):
            continue
        seen.add(pid)
        results.append({
            "id":        pid,
            "title":     title,
            "subreddit": _community(it),
            "score":     it.get("upVotes", 0),
            "comments":  it.get("numberOfComments", 0),
            "url":       it.get("url") or "",
            "selftext":  body[:400],
            "created":   created.strftime("%Y-%m-%d %H:%M UTC"),
        })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def fetch_reddit_comments(keywords: list[str], relevance_terms: list[str],
                          lookback_hours: int, apify_token: str | None = None,
                          max_wait_secs: int = 1200) -> list:
    """Single Apify run searching all keywords for comments. Returns shape compatible
    with the previous PRAW implementation (subreddit/body/score/url/created)."""
    apify_token = apify_token or os.getenv("APIFY_TOKEN", "")
    if not apify_token:
        print("      ⚠ APIFY_TOKEN missing — Reddit comments skipped.")
        return []
    try:
        items = _run_apify_reddit(
            {
                "searches": list(keywords),
                "searchPosts": False,
                "searchComments": True,
                "sort": "new",
                "maxItems":     25 * len(keywords),
                "maxComments":  25 * len(keywords),
                "proxy": {"useApifyProxy": True},
            },
            "comments", apify_token, max_wait_secs=max_wait_secs,
        )
    except Exception as e:
        print(f"      ⚠ Reddit comments actor failed: {e}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    seen: set[str] = set()
    results: list[dict] = []
    for it in items:
        if it.get("dataType") != "comment":
            continue
        cid = it.get("parsedId") or it.get("id") or ""
        if not cid or cid in seen:
            continue
        created = _parse_apify_ts(it.get("createdAt"))
        if created < cutoff:
            continue
        body = (it.get("body") or "")
        if not is_relevant(body, relevance_terms):
            continue
        seen.add(cid)
        results.append({
            "subreddit": _community(it),
            "body":      body[:400],
            "score":     it.get("upVotes", 0),
            "url":       it.get("url") or "",
            "created":   created.strftime("%Y-%m-%d %H:%M UTC"),
        })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
