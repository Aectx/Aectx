#!/usr/bin/env python3
"""Scrape the public contribution calendar. No token required.

GitHub serves the same fragment the profile page uses at
https://github.com/users/<username>/contributions
"""
import datetime
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "profile.json")) as f:
    USERNAME = json.load(f)["login"]

URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(HERE, "..", "data", "contributions.json")


def fetch_days():
    resp = requests.get(URL, headers={"User-Agent": "profile-readme-bot/1.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        print("no calendar cells found — GitHub markup may have changed", file=sys.stderr)
        sys.exit(1)

    days = []
    for td in cells:
        date = td.get("data-date")
        if not date:
            continue
        tooltip = soup.find("tool-tip", attrs={"for": td.get("id")}) if td.get("id") else None
        text = tooltip.get_text(" ", strip=True) if tooltip else ""
        if re.search(r"no contributions", text, re.I):
            count = 0
        else:
            match = re.search(r"(\d+)\s+contribution", text)
            count = int(match.group(1)) if match else 0
        days.append({
            "date": date,
            "count": count,
            "level": int(td.get("data-level") or 0),
        })
    days.sort(key=lambda d: d["date"])
    return days


def compute_current_streak(days):
    idx = len(days) - 1
    if days[idx]["count"] == 0:
        idx -= 1
    streak = 0
    end_idx = idx
    while idx >= 0 and days[idx]["count"] > 0:
        streak += 1
        idx -= 1
    if streak == 0:
        return 0, None, None
    return streak, days[idx + 1]["date"], days[end_idx]["date"]


def compute_longest_streak(days):
    longest = run = 0
    longest_start = longest_end = None
    run_start = None
    for i, day in enumerate(days):
        if day["count"] > 0:
            if run == 0:
                run_start = i
            run += 1
            if run > longest:
                longest = run
                longest_start = days[run_start]["date"]
                longest_end = days[i]["date"]
        else:
            run = 0
    return longest, longest_start, longest_end


def build_data(days):
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"] > 0)
    best = max(days, key=lambda d: d["count"])
    cur_len, cur_start, cur_end = compute_current_streak(days)
    long_len, long_start, long_end = compute_longest_streak(days)
    monthly = {}
    for day in days:
        key = day["date"][:7]
        monthly[key] = monthly.get(key, 0) + day["count"]
    return {
        "username": USERNAME,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "active_days": active,
        "current_streak": {"length": cur_len, "start": cur_start, "end": cur_end},
        "longest_streak": {"length": long_len, "start": long_start, "end": long_end},
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": [{"month": k, "total": v} for k, v in sorted(monthly.items())],
        "days": days,
    }


if __name__ == "__main__":
    days = fetch_days()
    data = build_data(days)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(
        f"wrote {OUT_PATH}: {data['total_contributions']} contributions, "
        f"current streak {data['current_streak']['length']}, "
        f"longest streak {data['longest_streak']['length']}"
    )
