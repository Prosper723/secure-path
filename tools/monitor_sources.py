"""
Secure Path — official source change monitor.

Re-fetches every official page the dataset relies on (embassy pages first), fingerprints
the readable text and compares it with the last run. Any change is flagged for human review
before the dataset is updated — the rules engine is never changed automatically.

Run:  python tools/monitor_sources.py            (first run records a baseline)
      python tools/monitor_sources.py --report   (show the last results without fetching)
"""

import hashlib
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "tools" / "source_fingerprints.json"


def sources_to_watch() -> dict:
    data = json.loads((ROOT / "countries.json").read_text(encoding="utf-8"))
    watch = {}
    for c in data["countries"]:
        ev = c.get("evidence")
        if ev:
            watch[ev["source"]["url"]] = f"{c['name']} — {ev['source']['label']}"
    for s in data["sources"].values():  # legal framework pages too
        if s.get("kind") == "official":
            watch.setdefault(s["url"], s["label"])
    return watch


def fingerprint(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "SecurePath-monitor/1.0 (research prototype)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    if url.lower().endswith(".pdf") or raw[:4] == b"%PDF":
        return hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8", errors="ignore")
    text = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", text)   # drop code
    text = re.sub(r"(?s)<[^>]+>", " ", text)                                     # drop tags
    text = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha256(text.encode()).hexdigest()


def main():
    old = json.loads(STATE.read_text()) if STATE.exists() else {}
    if "--report" in sys.argv:
        for url, v in old.items():
            print(f"{v.get('status', '?'):9} {v.get('checked', '?')}  {v.get('label', url)}")
        return
    new, changed = {}, []
    for url, label in sources_to_watch().items():
        try:
            fp = fingerprint(url)
            prev = old.get(url, {}).get("fingerprint")
            status = "NEW" if prev is None else ("CHANGED" if fp != prev else "same")
        except Exception as e:  # network errors are reported, never silently ignored
            fp, status = old.get(url, {}).get("fingerprint"), f"ERROR ({type(e).__name__})"
        new[url] = {"label": label, "fingerprint": fp, "status": status, "checked": date.today().isoformat()}
        print(f"{status:9} {label}")
        if status == "CHANGED":
            changed.append((label, url))
    STATE.write_text(json.dumps(new, indent=1))
    if changed:
        print("\n⚠ These official pages have changed. Review them, then update VERIFIED in "
              "tools/build_countries.py and rebuild countries.json:")
        for label, url in changed:
            print(f"  - {label}\n    {url}")
    else:
        print("\nNo changes detected." if old else "\nBaseline recorded. Run again later to detect changes.")


if __name__ == "__main__":
    main()
