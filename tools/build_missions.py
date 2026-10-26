"""
Secure Path — embassy & consulate directory builder.

Turns the FCDO's published lists into missions.json, so travellers see the right
embassy, consulates and honorary consuls for their destination — no downloads needed.

Inputs (GOV.UK, "Foreign embassies in the UK"), put them in tools/fcdo_lists/:
  * LONDON_DIPLOMATIC_LIST_*.odt      embassies / high commissions and their consular sections
  * CONSULATES_OUTSIDE_LONDON_*.odt   career consulates in other UK cities
  * HONORARY_CONSULS_LIST_*.odt       honorary consulates
  * Heads_of_Mission_Master_List_*.ods  used only for "no embassy in London" (non-resident) flags

Privacy: only PUBLIC OFFICE contact details are kept. Names of diplomats and their spouses
are deliberately dropped — travellers don't need them and they are personal data.

Run:  python tools/build_missions.py
"""

import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
LISTS = ROOT / "tools" / "fcdo_lists"
OUT = ROOT / "missions.json"
sys.path.insert(0, str(ROOT))
from data import COUNTRIES  # noqa: E402

NS = {"text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
      "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
      "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0"}


# ── Reading OpenDocument files without extra libraries ──────────────────────
def _render(el, parts: list) -> None:
    """Flatten an ODF element into text, honouring <text:s/> (spaces), tabs and line breaks."""
    tag = el.tag.split("}")[-1]
    if tag == "s":
        parts.append(" " * int(el.get(f"{{{NS['text']}}}c", "1")))
    elif tag == "tab":
        parts.append(" ")
    elif tag == "line-break":
        parts.append("\n")
    elif tag in ("note", "annotation", "tracked-changes"):
        pass  # footnotes / comments are not contact details
    else:
        if el.text:
            parts.append(el.text)
        for child in el:
            _render(child, parts)
            if child.tail:
                parts.append(child.tail)
            continue
    return


def odt_lines(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("content.xml"))
    lines = []
    for el in root.iter():
        if el.tag.split("}")[-1] not in ("p", "h"):
            continue
        parts: list = []
        _render(el, parts)
        for ln in "".join(parts).split("\n"):
            ln = re.sub(r"\s+", " ", ln.replace("\xa0", " ")).strip()
            if ln:
                lines.append(ln)
    return lines


def docx_lines(path: Path) -> list[str]:
    """GOV.UK sometimes publishes these lists as Word files instead of OpenDocument."""
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    lines = []
    for para in root.iter(f"{{{W}}}p"):
        parts = []
        for node in para.iter():
            tag = node.tag.split("}")[-1]
            if tag == "t" and node.text:
                parts.append(node.text)
            elif tag == "tab":
                parts.append(" ")
            elif tag in ("br", "cr"):
                parts.append("\n")
        for ln in "".join(parts).split("\n"):
            ln = re.sub(r"\s+", " ", ln.replace("\xa0", " ")).strip()
            if ln:
                lines.append(ln)
    return lines


def read_lines(path: Path) -> list[str]:
    return docx_lines(path) if path.suffix.lower() == ".docx" else odt_lines(path)


def ods_rows(path: Path, sheet: str) -> list[list[str]]:
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("content.xml"))
    for t in root.iter(f"{{{NS['table']}}}table"):
        if t.get(f"{{{NS['table']}}}name") != sheet:
            continue
        rows = []
        for r in t.iter(f"{{{NS['table']}}}table-row"):
            row = []
            for c in r.iter(f"{{{NS['table']}}}table-cell"):
                rep = int(c.get(f"{{{NS['table']}}}number-columns-repeated", "1"))
                val = " ".join("".join(p.itertext()) for p in c.iter(f"{{{NS['text']}}}p")).strip()
                row += [val] * min(rep, 50)
            if any(row):
                rows.append(row)
        return rows
    return []


# ── Country headings → ISO codes ────────────────────────────────────────────
HEADING_ALIASES = {
    "THE BAHAMAS": "BS", "BAHAMAS": "BS", "BRUNEI": "BN", "BRUNEI DARUSSALAM": "BN", "CAPE VERDE": "CV",
    "CABO VERDE": "CV", "CONGO": "CG", "CONGO (REPUBLIC OF)": "CG", "REPUBLIC OF THE CONGO": "CG",
    "CONGO (DEMOCRATIC REPUBLIC OF)": "CD", "DEMOCRATIC REPUBLIC OF THE CONGO": "CD", "DEMOCRATIC REPUBLIC OF CONGO": "CD",
    "COTE D'IVOIRE": "CI", "CÔTE D'IVOIRE": "CI", "COTE D’IVOIRE": "CI", "CÔTE D’IVOIRE": "CI", "IVORY COAST": "CI",
    "CZECH REPUBLIC": "CZ", "CZECHIA": "CZ", "EAST TIMOR": "TL", "TIMOR-LESTE": "TL", "ESWATINI": "SZ",
    "THE GAMBIA": "GM", "GAMBIA": "GM", "HOLY SEE": "VA", "IRAN": "IR", "KOREA": "KR", "KOREA (REPUBLIC OF)": "KR",
    "REPUBLIC OF KOREA": "KR", "SOUTH KOREA": "KR", "KOREA (DEMOCRATIC PEOPLE'S REPUBLIC OF)": "KP",
    "DEMOCRATIC PEOPLE'S REPUBLIC OF KOREA": "KP", "NORTH KOREA": "KP", "KYRGYZSTAN": "KG", "KYRGYZ REPUBLIC": "KG",
    "LAOS": "LA", "LAO PEOPLE'S DEMOCRATIC REPUBLIC": "LA", "MACEDONIA": "MK", "NORTH MACEDONIA": "MK",
    "MICRONESIA": "FM", "MOLDOVA": "MD", "PALESTINE": "PS", "PALESTINIAN MISSION": "PS", "RUSSIA": "RU",
    "RUSSIAN FEDERATION": "RU", "ST KITTS AND NEVIS": "KN", "ST CHRISTOPHER AND NEVIS": "KN",
    "ST CHRISTOPHER & NEVIS": "KN", "SAINT KITTS AND NEVIS": "KN", "ST LUCIA": "LC", "SAINT LUCIA": "LC",
    "ST VINCENT AND THE GRENADINES": "VC", "SAINT VINCENT AND THE GRENADINES": "VC", "SYRIA": "SY",
    "TANZANIA": "TZ", "TURKEY": "TR", "TÜRKIYE": "TR", "TURKIYE": "TR", "UNITED STATES": "US",
    "UNITED STATES OF AMERICA": "US", "USA": "US", "VIETNAM": "VN", "VIET NAM": "VN", "VATICAN": "VA",
    "SAO TOME AND PRINCIPE": "ST", "SÃO TOMÉ AND PRÍNCIPE": "ST", "BOSNIA AND HERZEGOVINA": "BA",
    "BOSNIA & HERZEGOVINA": "BA", "ANTIGUA & BARBUDA": "AG", "TRINIDAD & TOBAGO": "TT", "KOSOVO": "XK",
    "TAIWAN": "TW", "TAIPEI REPRESENTATIVE OFFICE": "TW", "CONGO (DEMOCRATIC REPUBLIC)": "CD",
    "KOREA (NORTH)": "KP", "KOREA (SOUTH)": "KR", "SLOVAK REPUBLIC": "SK", "CENTRAL AFRICAN REPUBLIC": "CF",
    "MARSHALL ISLANDS": "MH", "FEDERATED STATES OF MICRONESIA": "FM", "SAINT CHRISTOPHER AND NEVIS": "KN",
}
_BY_NAME = {c["name"].upper(): iso for iso, c in COUNTRIES.items()}


def _norm(name: str) -> str:
    import unicodedata
    k = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().upper()
    k = k.replace("&", " AND ").replace("’", "'").replace("~", "")
    k = re.sub(r"\((REALM|NR|CLOSED|REPUBLIC OF|UNION OF|STATE OF|KINGDOM OF)\)", "", k)
    k = re.sub(r",\s*(COMMONWEALTH|REPUBLIC|KINGDOM|STATE|FEDERATION|UNION) OF$", "", k)
    k = re.sub(r"^(THE |REPUBLIC OF |KINGDOM OF |STATE OF )", "", k)
    return re.sub(r"\s+", " ", k).strip(" .:,")


_NORM_INDEX = {**{_norm(c["name"]): iso for iso, c in COUNTRIES.items()},
               **{_norm(k): v for k, v in HEADING_ALIASES.items()}}


def heading_iso(line: str):
    if not line or line != line.upper() or not re.search(r"[A-Z]", line) or len(line) > 60:
        return None
    return _NORM_INDEX.get(_norm(line))


# ── Field recognisers ───────────────────────────────────────────────────────
PERSON = re.compile(
    r"^(HIS|HER|THEIR) |^(Mr|Mrs|Ms|Miss|Mx|Dr|Prof|Professor|Sir|Dame|Lady|Lord|Colonel|Col|Lieutenant|Lieutnant|Lt|"
    r"Major|Maj|Captain|Capt|Commander|Cdr|Brigadier|Brig|General|Gen|Admiral|Rear|Vice|Air|Group|Wing|Sheikh|Shaikh|"
    r"Shaikha|Sheikha|H\.?S\.?H\.?|H\.?R\.?H\.?|S\.?E\.?|Rev|Revd|Father|Monsignor|Archbishop|Judge|HE|H\.E\.|Hon|Rt|Dato|Datin|Tan Sri|Ambassador|Mme|"
    r"Mademoiselle|Madame|Doctor|Chief|Pastor|Imam|Prince|Princess|HRH|Count|Countess|Baron|Baroness|Vacant)\b\.?\s", re.I)
PHONE = re.compile(r"^(phone|tel|telephone|t|ftel|mobile|mob|whatsapp)\b[^:\d@]{0,30}[:.]?\s*(.*)$", re.I)
FAX = re.compile(r"^fax\b", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
WEB = re.compile(r"((?:https?://|www\.)[^\s,;]+)", re.I)
HOURS = re.compile(r"\b(mon|monday|tue|wed|thu|fri|friday|sat|sun|hours|opening|\d{1,2}[.:]\d{2}\s*[-–]\s*\d)", re.I)
CONSULAR_SECTION = re.compile(r"^(consular|visa|passport|consulate|home affairs|immigration)", re.I)
OTHER_SECTION = re.compile(r"(attach[eé]|defence|military|naval|police|liaison|trade|commercial|economic|cultural|"
                           r"press|investment|tourism|education|agricultur|health|finance|science|office of the|"
                           r"political|policy|research|administration|protocol|chancery|media|information|"
                           r"ambassador'?s office|maritime|security|legal|labour|social)", re.I)
ROLE = re.compile(r"\b(honorary (vice[- ])?consul|consul[- ]general|vice[- ]consul|consul\b|head of consular post|"
                  r"with (the )?responsibility for|ambassador|high commissioner|charg[eé] d|attach[eé]|"
                  r"counsellor|secretary)\b", re.I)


def is_person(ln: str) -> bool:
    """Lines naming people (any title, any capitalisation) — never kept."""
    office = re.match(r"^(the )?(office|embassy|high commission|consulate|honorary consulate|consular|mission|"
                      r"delegation|representation|permanent|chancery|assistant high commission|deputy high commission)",
                      ln, re.I)
    if PERSON.match(ln) or (ROLE.search(ln) and not office):
        return True
    words = re.findall(r"[A-Za-z]+", ln)
    return len(words) >= 2 and ln.isupper() and not re.search(r"\d", ln)   # NAMES IN CAPITALS


RESPONSIBILITY = re.compile(r"with (?:the )?responsibility for (.+?)(?:\s*\((?:since|from)\b.*)?$", re.I)
CLOSED = re.compile(r"temporarily (closed|ceased)|\bclosed\b", re.I)


def parse_contact(lines: list[str]) -> dict:
    """Turn the lines of one office into a contact record (no personal names)."""
    rec = {"name": lines[0] if lines else "", "address": [], "phone": [], "email": [], "website": None,
           "hours": [], "status": None}
    for ln in lines[1:]:
        ln = re.sub(r"^address\s*:\s*", "", ln, flags=re.I)
        if re.search(r"see honorary consuls|honorary consul(ate)? (of|for|in)\b", ln, re.I):
            continue          # cross-reference / repeated office name, not an address line
        if re.fullmatch(r"(\+|00)\s?\d[\d\s().\/-]{6,}", ln.strip(" -")):
            rec["phone"].append(ln.strip(" -"))   # international number
            continue
        if "@" in ln:
            ln = re.sub(r"(@[\w-]+),(\w{2,4})\b", r"\1.\2", ln)        # "gmail,com" typo in source
        low = ln.lower()
        if re.match(r"^emergency", low) and re.search(r"\d{4}", ln):
            rec["phone"].append(re.sub(r"^[^:]*:\s*", "", ln) + " (emergency)")
            continue
        if PHONE_IN.search(ln) and re.search(r"\b(phone|tel|te/faxl|direct|emergency|mobile|mob|whatsapp|fax)\b", low):
            if not re.match(r"^\s*fax\b", low):
                label = "emergency" if "emergency" in low else None
                rec["phone"].append(PHONE_IN.search(ln).group(0).strip() + (f" ({label})" if label else ""))
            continue
        if re.fullmatch(r"[\w-]+(\.[\w-]+)+\.(gov|org|com|net|int|gouv|go)(\.[a-z]{2})?/?\S*", ln, re.I) and not rec["website"]:
            rec["website"] = "https://" + ln   # bare domain without www
            continue
        if re.match(r"^\(?temporarily (closed|ceased)", ln, re.I) or (CLOSED.search(ln) and len(ln) < 60):
            rec["status"] = "Temporarily closed" if re.search(r"temporarily", ln, re.I) else ln.strip("()")
            continue
        if FAX.match(ln):
            continue
        m = PHONE.match(ln)
        if m:
            num = re.sub(r"[^\d+ ()/-]", "", m.group(2)).strip(" /-")
            if re.search(r"\d{5,}", num.replace(" ", "")):
                rec["phone"].append(num)
            continue
        emails = EMAIL.findall(ln)
        if emails:
            rec["email"] += [e.rstrip(".") for e in emails]
            continue
        w = WEB.search(ln)
        if w and not rec["website"]:
            url = w.group(1).rstrip(".")
            rec["website"] = url if url.startswith("http") else "https://" + url
            continue
        if low.startswith(("web", "website", "email", "e-mail", "tel", "phone")):
            continue  # empty label
        if HOURS.search(ln) and re.search(r"\d", ln):
            rec["hours"].append(ln)
            continue
        if ln.startswith("@") or re.fullmatch(r"@\w+", ln):     # social media handle
            continue
        pm = PHONE_IN.search(ln)
        if pm and len(re.sub(r"[^A-Za-z]", "", PHONE_IN.sub("", ln).split("(")[0])) <= 3:
            label = re.search(r"\(([^)]+)\)", ln)          # e.g. "0871 376 0023 (Visa Information)"
            rec["phone"].append(pm.group(0).strip() + (f" ({label.group(1)})" if label else ""))
            continue
        rec["address"].append(ln)
    rec["address"] = ", ".join(a.rstrip(",") for a in rec["address"][:6])
    rec["email"] = list(dict.fromkeys(rec["email"]))[:2]
    rec["phone"] = list(dict.fromkeys(rec["phone"]))[:2]
    return rec


PHONE_IN = re.compile(r"(?:\+44\s?\(?0?\)?\s?|0)\d{2,4}[\s-]?\d{3,4}[\s-]?\d{2,4}")
UK_POSTCODE = re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b")


# ── London Diplomatic List ──────────────────────────────────────────────────
def parse_london(lines):
    out, iso, block = {}, None, []

    def flush():
        if iso is None or not block:
            return
        # stop at the first person line — everything after is staff
        contact_lines = []
        for ln in block:
            if is_person(ln):
                break
            contact_lines.append(ln)
        status = None
        if contact_lines and CLOSED.search(contact_lines[0]) and len(contact_lines[0]) < 40:
            status = contact_lines.pop(0).strip("()")
        # split into the main mission and named sections
        sections, cur = [], []
        for ln in contact_lines:
            is_section = (CONSULAR_SECTION.match(ln) or OTHER_SECTION.search(ln)
                          or re.search(r"\b(section|office|department|division|unit|desk)\b\s*(\(.*\))?$", ln, re.I))
            if cur and is_section and len(ln) < 70 and not EMAIL.search(ln) and not PHONE.match(ln) \
                    and not UK_POSTCODE.search(ln) and not PHONE_IN.search(ln):
                if len(cur) == 1 and len(sections) > 0:      # two headings in a row → one section
                    cur[0] = f"{cur[0]} — {ln}"
                else:
                    sections.append(cur); cur = [ln]
            else:
                cur.append(ln)
        if cur:
            sections.append(cur)
        if not sections:
            return  # heading with no contact details (e.g. staff only)
        main = parse_contact(sections[0])
        main["status"] = main["status"] or status
        if re.search(r"see honorary consuls", main["name"], re.I):
            main = None   # no embassy — only an honorary consul (listed separately)
        rec = {"embassy": main, "consular": []}
        for sec in sections[1:]:
            if CONSULAR_SECTION.match(sec[0]) or re.search(r"\b(visa|consular|passport)", sec[0], re.I):
                c = parse_contact(sec)
                if not c["address"] and main:
                    c["address"] = main["address"]
                rec["consular"].append(c)
        if iso not in out:          # first (main-list) record wins
            out[iso] = rec
        _SEEN.add(iso)

    for ln in lines:
        in_staff = any(is_person(b) for b in block)
        h = heading_iso(ln) or (mission_line_iso(ln, iso) if in_staff else None)
        if h:
            flush(); iso, block = h, []
            if not heading_iso(ln):
                block.append(ln)   # the mission line itself is the first contact line
        elif iso:
            block.append(ln)
    flush()
    return out


_NAMES_LONGEST = sorted(_NORM_INDEX.items(), key=lambda kv: -len(kv[0]))


def mission_line_iso(line: str, current):
    """'Embassy of the Republic of South Sudan' with no heading above it → new country block."""
    if not re.match(r"^(Embassy|High Commission|Permanent Mission)\b", line):
        return None
    n = " " + _norm(line) + " "
    for name, iso in _NAMES_LONGEST:
        if len(name) > 3 and f" {name} " in n:
            return iso if iso != current and iso not in _SEEN else None
    return None


_SEEN: set = set()


def split_london(lines):
    """The London list = embassies, then appendices. Keep the embassy part and the
    'HONORARY CONSULS' (in London) appendix; ignore national days, international
    organisations, Agents General (state/provincial offices) and territories."""
    end = next((i for i, l in enumerate(lines) if l.startswith("LIST OF THE REPRESENTATIVES")
                or l.startswith("NATIONAL AND OTHER RELATED DAYS")), len(lines))
    main = lines[:end]
    try:
        h0 = next(i for i, l in enumerate(lines) if l == "HONORARY CONSULS" and i > end)
        h1 = next(i for i, l in enumerate(lines) if i > h0 and l.isupper() and not heading_iso(l)
                  and len(l) > 8 and not PERSON.match(l))
    except StopIteration:
        return main, {}
    honorary, iso, block = {}, None, []

    def flush():
        if iso and block and not block[0].lower().startswith("vacant"):
            body = [b for b in block if not is_person(b)]
            if body:
                c = parse_contact([f"Honorary Consulate in London"] + body)
                c.update(city="London", kind="honorary", area=None)
                if all(c["address"] != o["address"] for o in honorary.get(iso, [])):
                    honorary.setdefault(iso, []).append(c)

    for ln in lines[h0 + 1:h1]:
        h = heading_iso(ln)
        if h:
            flush(); iso, block = h, []
        elif iso:
            block.append(ln)
    flush()
    return main, honorary


# ── Consulates outside London / honorary consuls ────────────────────────────
OFFICE_START = re.compile(r"^(honorary |assistant |deputy |vice[- ]?)*(consulate|consular|vice[- ]consulate|"
                          r"high commission|commission|agency|office)\b.*\bin\b", re.I)
NOT_UK = re.compile(r"bermuda|cayman|gibraltar|jersey|guernsey|isle of man|falkland|turks|caicos|providenciales|"
                    r"virgin islands|anguilla|montserrat|st helena|saint helena|ascension|tristan|pitcairn|"
                    r"akrotiri|dhekelia|sark|alderney|douglas|st peter port|st helier|hamilton|george town|tortola",
                    re.I)


def parse_offices(lines, kind):
    out, iso, entry = {}, None, None

    def flush():
        nonlocal entry
        if iso and entry:
            name = entry[0]
            city = re.split(r"\bin\b", name, flags=re.I)[-1].strip(" ()")
            city = re.sub(r"\(.*?\)", "", city).strip()
            responsibility = None
            body = []
            for ln in entry[1:]:
                if re.match(r"^temporarily (closed|ceased)", ln, re.I):
                    body.append(ln); continue
                if is_person(ln):
                    m = RESPONSIBILITY.search(ln)
                    if m and not responsibility:
                        responsibility = m.group(1).strip(" .")
                    continue
                body.append(ln)
            c = parse_contact([name] + body)
            text = name + " " + c["address"]
            if not NOT_UK.search(text):
                c.update(city=city, kind=kind, area=responsibility)
                if all(c["address"] != o["address"] or c["city"] != o["city"] for o in out.get(iso, [])):
                    out.setdefault(iso, []).append(c)
        entry = None

    for ln in lines:
        h = heading_iso(ln)
        if h:
            flush(); iso = h
        elif iso and OFFICE_START.match(ln):
            flush(); entry = [ln]
        elif iso and entry is not None:
            entry.append(ln)
    flush()
    return out


# ── Heads of Mission: non-resident / closed flags ───────────────────────────
def parse_hom(path):
    rows = ods_rows(path, "HoM_Contact_Details")
    head = [h.strip().upper() for h in rows[0]]
    ci, ni = head.index("COUNTRY"), head.index("NON-RESIDENT?")
    flags = {}
    for r in rows[1:]:
        if len(r) <= max(ci, ni):
            continue
        raw = r[ci].strip()
        closed = "CLOSED" in raw.upper()
        name = re.sub(r"\((CLOSED|NR|REALM)\)", "", raw, flags=re.I).strip()
        iso = _NORM_INDEX.get(_norm(name))
        if not iso:
            continue
        nr = r[ni].strip()
        flags[iso] = {"non_resident_in": nr if nr and nr != "-" else None, "closed": closed}
    return flags


def main():
    def find(stem, exts=(".odt", ".docx")):
        """Newest file (by modification time) whose name contains `stem`, in any supported format."""
        hits = [p for p in LISTS.iterdir() if stem.lower() in p.name.lower() and p.suffix.lower() in exts]
        if not hits:
            sys.exit(f"Missing a '{stem}' file ({'/'.join(exts)}) in {LISTS}")
        return max(hits, key=lambda p: p.stat().st_mtime)

    london_file = find("LONDON_DIPLOMATIC_LIST")
    all_london = read_lines(london_file)
    london_main, london_honorary = split_london(all_london)
    london = parse_london(london_main)
    consulates = parse_offices(read_lines(find("CONSULATES_OUTSIDE_LONDON")), "consulate")
    honorary = parse_offices(read_lines(find("HONORARY_CONSUL")), "honorary")
    hom = parse_hom(find("Heads_of_Mission", (".ods",)))

    missions = {}
    for iso in COUNTRIES:
        if iso == "GB":
            continue
        rec = london.get(iso, {"embassy": None, "consular": []})
        rec["consulates"] = consulates.get(iso, [])
        rec["honorary"] = london_honorary.get(iso, []) + honorary.get(iso, [])
        rec.update(hom.get(iso, {"non_resident_in": None, "closed": False}))
        if any([rec["embassy"], rec["consulates"], rec["honorary"], rec["non_resident_in"]]):
            missions[iso] = rec

    meta = {"source": "FCDO London Diplomatic List, Consulates outside London and Honorary Consuls list",
            "revised": next((re.sub(r"(?i)^revised\s+", "", l).title() for l in all_london[:5]
                             if l.upper().startswith("REVISED")), "unknown"),
            "url": "https://www.gov.uk/government/publications/foreign-embassies-in-the-uk"}
    OUT.write_text(json.dumps({"meta": meta, "missions": missions}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {OUT.name}: {len(missions)} countries · "
          f"{sum(1 for m in missions.values() if m['embassy'])} embassies · "
          f"{sum(len(m['consulates']) for m in missions.values())} consulates · "
          f"{sum(len(m['honorary']) for m in missions.values())} honorary consulates (UK only)")


if __name__ == "__main__":
    main()
