#!/usr/bin/env python3
"""
Pulls active-user counts from the Chrome Web Store for each extension and
writes them to data/installs.json in this repo. A GitHub Action commits the
updated file daily; shields.io dynamic-json badges in the README read it
straight from raw.githubusercontent.com.

Chrome Web Store markup changes occasionally — if a count comes back as
None, open the item page, view source, and update EXTRACT_PATTERN below to
match the current markup before re-running.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

# label -> Chrome Web Store item URL
EXTENSIONS = {
    "apexgenie": "https://chromewebstore.google.com/detail/json-to-apex-genie/ifliljlnfdnmagdgmomglfoimjcnpinb",
    "sfvault": "https://chromewebstore.google.com/detail/jpdnbaplnomajdlomcmbpfklcolgbljo",
    "sfsecurityauditor": "https://chromewebstore.google.com/detail/mbanedjmimggapgpcnlhbndmdmehpolj",
    "sldsiconskit": "https://chromewebstore.google.com/detail/pgjeeljfclipedfnlojjchmmilddiaje",
    "fieldforge": "https://chromewebstore.google.com/detail/nfjjccdcnpdmfglblfnkmmfecmblbhfo",
}

# Matches strings like "10,000+ users" in the item page markup.
EXTRACT_PATTERN = re.compile(r'([\d,]+)\+?\s*users', re.IGNORECASE)

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "installs.json"


def fetch_user_count(url: str) -> int | None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as exc:  # network or HTTP error
        print(f"  fetch failed for {url}: {exc}", file=sys.stderr)
        return None

    match = EXTRACT_PATTERN.search(html)
    if not match:
        print(f"  no user-count match for {url} — markup may have changed", file=sys.stderr)
        return None

    return int(match.group(1).replace(",", ""))


def main() -> None:
    results = {}
    total = 0

    for label, url in EXTENSIONS.items():
        print(f"Fetching {label}...")
        count = fetch_user_count(url)
        results[label] = {"users": count if count is not None else 0}
        if count:
            total += count

    results["total"] = {"users": total}

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(results, indent=2) + "\n")
    print(f"Wrote {OUTPUT_PATH} — total users: {total}")


if __name__ == "__main__":
    main()
