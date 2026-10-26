"""
Secure Path — check GOV.UK for new embassy & consulate lists.

Asks GOV.UK's public Content API whether the "Foreign embassies in the UK" publication has
new files. If it has, it shows what changed, downloads the new lists into tools/fcdo_lists/,
rebuilds missions.json and reports which countries' contact details changed.

Run:  python tools/check_fcdo_updates.py            (check, then ask before downloading)
      python tools/check_fcdo_updates.py --yes      (download and rebuild without asking)
      python tools/check_fcdo_updates.py --check    (only report; exit code 1 if updates exist)
"""

import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LISTS = ROOT / "tools" / "fcdo_lists"
ARCHIVE = LISTS / "archive"
STATE = LISTS / "gov_uk_state.json"
API = "https://www.gov.uk/api/content/government/publications/foreign-embassies-in-the-uk"
PAGE = "https://www.gov.uk/government/publications/foreign-embassies-in-the-uk"

# Which GOV.UK attachment is which list (matched on the attachment title)
WANTED = {
    "london": ("london diplomatic list", "LONDON_DIPLOMATIC_LIST"),
    "consulates": ("consular offices outside london", "CONSULATES_OUTSIDE_LONDON"),
    "honorary": ("honorary consul", "HONORARY_CONSUL"),
    "heads": ("heads of mission", "Heads_of_Mission"),
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "SecurePath-update-check/1.0 (research prototype)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def latest_attachments(content: dict) -> dict:
    found = {}
    for att in content.get("details", {}).get("attachments", []):
        title = (att.get("title") or "").lower()
        for key, (needle, _) in WANTED.items():
            if needle in title and key not in found:
                found[key] = {"title": att.get("title"), "url": att.get("url")}
    return found


def contact_snapshot() -> dict:
    p = ROOT / "missions.json"
    if not p.exists():
        return {}
    m = json.loads(p.read_text(encoding="utf-8"))["missions"]
    snap = {}
    for iso, r in m.items():
        e = r.get("embassy") or {}
        snap[iso] = (e.get("address"), tuple(e.get("phone") or []), tuple(e.get("email") or []),
                     len(r.get("consulates", [])), len(r.get("honorary", [])))
    return snap


def main():
    auto, check_only = "--yes" in sys.argv, "--check" in sys.argv
    print("Checking GOV.UK for new embassy and consulate lists…")
    try:
        content = json.loads(fetch(API))
    except Exception as e:
        print(f"Couldn't reach GOV.UK ({type(e).__name__}). Check your internet connection and try again.")
        sys.exit(2)

    updated = content.get("public_updated_at", "?")
    history = content.get("details", {}).get("change_history", [])
    atts = latest_attachments(content)
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    local = {p.name for p in LISTS.iterdir() if p.is_file()} if LISTS.exists() else set()

    new = {k: a for k, a in atts.items() if a["url"].rsplit("/", 1)[-1] not in local
           and a["url"] != state.get("files", {}).get(k)}

    print(f"GOV.UK page last updated: {updated[:10]}")
    since = state.get("public_updated_at")
    notes = [h for h in history if not since or h.get("public_timestamp", "") > since][:5]
    for h in notes:
        print(f"  • {h.get('public_timestamp', '')[:10]}: {h.get('note', '').strip()}")

    if not new:
        print("\n✓ You already have the latest lists. Nothing to do.")
        STATE.write_text(json.dumps({"public_updated_at": updated,
                                     "files": {k: a["url"] for k, a in atts.items()}}, indent=1))
        return
    print("\nNew files available:")
    for k, a in new.items():
        print(f"  • {a['title']}\n    {a['url']}")
    if check_only:
        sys.exit(1)
    if not auto and input("\nDownload them and rebuild the contact directory? [y/N] ").strip().lower() != "y":
        print(f"No changes made. You can also download them yourself from {PAGE}")
        return

    before = contact_snapshot()
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    for k, a in new.items():
        stem = WANTED[k][1]
        for old in LISTS.iterdir():          # move the previous version of this list out of the way
            if old.is_file() and stem.lower() in old.name.lower():
                shutil.move(str(old), ARCHIVE / old.name)
        name = a["url"].rsplit("/", 1)[-1]
        (LISTS / name).write_bytes(fetch(a["url"]))
        print(f"  ↓ {name}")

    print("\nRebuilding missions.json…")
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "build_missions.py")], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        print("⚠ The rebuild failed — the format may have changed. Your previous files are in tools/fcdo_lists/archive/.")
        sys.exit(3)

    after = contact_snapshot()
    changed = sorted(iso for iso in set(before) | set(after) if before.get(iso) != after.get(iso))
    print(f"\n{len(changed)} countries' contact details changed" + (": " + ", ".join(changed) if changed else "."))
    print("Run the tests (python -m pytest -q) and spot-check a few countries in the app before sharing it.")
    STATE.write_text(json.dumps({"public_updated_at": updated,
                                 "files": {k: a["url"] for k, a in atts.items()}}, indent=1))


if __name__ == "__main__":
    main()
