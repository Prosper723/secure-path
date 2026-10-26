"""
Secure Path — embassy & consulate directory.

Reads missions.json (built from the FCDO's official lists by tools/build_missions.py)
and answers one question: "who do I contact for this country, and which office is nearest me?"
"""

import json
import math
import re
from pathlib import Path
from urllib.parse import quote_plus

_DATA = json.loads((Path(__file__).parent / "missions.json").read_text(encoding="utf-8"))
MISSIONS: dict = _DATA["missions"]
META: dict = _DATA["meta"]

# Approximate coordinates (lat, lon) — used only to rank offices by distance.
COORDS = {
    "London": (51.507, -0.128), "Manchester": (53.481, -2.242), "Birmingham": (52.486, -1.890),
    "Leeds": (53.800, -1.549), "Liverpool": (53.408, -2.991), "Newcastle": (54.978, -1.618),
    "Sheffield": (53.381, -1.470), "Bradford": (53.795, -1.759), "Nottingham": (52.954, -1.158),
    "Leicester": (52.637, -1.140), "Coventry": (52.407, -1.512), "Bristol": (51.454, -2.588),
    "Cardiff": (51.481, -3.179), "Swansea": (51.621, -3.944), "Glasgow": (55.864, -4.252),
    "Edinburgh": (55.953, -3.188), "Aberdeen": (57.150, -2.094), "Inverness": (57.478, -4.224),
    "Belfast": (54.597, -5.930), "Londonderry": (54.997, -7.309), "Southampton": (50.910, -1.404),
    "Plymouth": (50.376, -4.143), "Hull": (53.767, -0.327), "Preston": (53.763, -2.703),
    "Norwich": (52.630, 1.297), "Cambridge": (52.205, 0.122), "Oxford": (51.752, -1.258),
    "Milton Keynes": (52.041, -0.759), "Northampton": (52.240, -0.903), "Peterborough": (52.573, -0.241),
    "Chester": (53.191, -2.892), "Bath": (51.381, -2.359), "Cheltenham": (51.900, -2.078),
    "Canterbury": (51.280, 1.079), "Dover": (51.128, 1.313), "Rochester": (51.388, 0.506),
    "Ashford": (51.146, 0.875), "Greenhithe": (51.450, 0.282), "Watford": (51.656, -0.390),
    "Woking": (51.319, -0.558), "Winchester": (51.060, -1.311), "Bedford": (52.136, -0.460),
    "Torquay": (50.462, -3.525), "Penzance": (50.118, -5.537), "Trowbridge": (51.319, -2.208),
    "Newhaven": (50.795, 0.055), "Angmering": (50.828, -0.488), "West Sussex": (50.920, -0.460),
    "Kent": (51.270, 0.700), "Sheringham": (52.943, 1.209), "Grimsby": (53.567, -0.080),
    "Immingham": (53.612, -0.217), "Barrow on Humber": (53.676, -0.383), "Beverley": (53.841, -0.432),
    "Malton": (54.135, -0.798), "Stirling": (56.117, -3.937), "Dunblane": (56.186, -3.965),
    "Kilsyth": (55.976, -4.058), "Cardross": (55.963, -4.652), "Fife": (56.250, -3.200),
    "Stornoway": (58.209, -6.387), "Kirkwall": (58.981, -2.960), "Lerwick": (60.155, -1.145),
    "Bangor": (54.660, -5.668), "Coleraine": (55.133, -6.668), "Newry": (54.176, -6.349),
    "Dundonald": (54.594, -5.810), "Barry": (51.400, -3.270), "Cwmbran": (51.654, -3.021),
    "Ceredigion": (52.250, -4.000), "Woodlands": (51.500, -0.300), "West Midlands": (52.486, -1.890),
}

# Where someone lives → words that appear in consulates' official "responsibility" areas
REGION_WORDS = {
    "London": ["london", "south east", "england"],
    "Manchester": ["manchester", "north west", "northwest", "lancashire", "cheshire", "england"],
    "Liverpool": ["liverpool", "merseyside", "north west", "northwest", "england"],
    "Preston": ["lancashire", "north west", "northwest", "england"],
    "Chester": ["cheshire", "north west", "northwest", "england"],
    "Leeds": ["leeds", "yorkshire", "england"], "Bradford": ["bradford", "yorkshire", "england"],
    "Sheffield": ["sheffield", "yorkshire", "england"], "Hull": ["hull", "humber", "yorkshire", "england"],
    "Newcastle": ["newcastle", "tyne", "north east", "northumberland", "durham", "england"],
    "Birmingham": ["birmingham", "west midlands", "midlands", "england"],
    "Coventry": ["coventry", "west midlands", "midlands", "england"],
    "Nottingham": ["nottingham", "east midlands", "midlands", "england"],
    "Leicester": ["leicester", "east midlands", "midlands", "england"],
    "Bristol": ["bristol", "south west", "avon", "england"], "Plymouth": ["plymouth", "devon", "south west", "england"],
    "Southampton": ["southampton", "hampshire", "south", "england"], "Norwich": ["norfolk", "east anglia", "england"],
    "Cambridge": ["cambridge", "east anglia", "east of england", "england"], "Oxford": ["oxford", "south east", "england"],
    "Cardiff": ["cardiff", "wales"], "Swansea": ["swansea", "wales"],
    "Glasgow": ["glasgow", "scotland"], "Edinburgh": ["edinburgh", "scotland"], "Aberdeen": ["aberdeen", "scotland"],
    "Belfast": ["belfast", "northern ireland"],
}
UK_CITIES = sorted(REGION_WORDS)

_ALIASES = {"newcastle upon tyne": "Newcastle", "newcastle-upon-tyne": "Newcastle", "kingston-upon-hull": "Hull",
            "the west midlands": "West Midlands", "northern ireland": "Belfast", "leicester and midlands": "Leicester",
            "lerwick (shetland": "Lerwick", "edinburgh, glasgow and aberdeen": "Edinburgh", "uk": "London"}


def clean_city(city: str) -> str:
    c = re.sub(r"^the\s+", "", city.strip(), flags=re.I)
    return _ALIASES.get(city.strip().lower(), _ALIASES.get(c.lower(), c.title() if c.islower() else c))


def _km(a: str, b: str):
    if a not in COORDS or b not in COORDS:
        return None
    (la1, lo1), (la2, lo2) = COORDS[a], COORDS[b]
    p1, p2, dl = math.radians(la1), math.radians(la2), math.radians(lo2 - lo1)
    return 6371 * math.acos(min(1, math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * math.cos(dl)))


def maps_url(address: str) -> str:
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(address)


def tel_url(phone: str) -> str:
    digits = re.sub(r"[^\d+]", "", phone.split("(")[0])
    if digits.startswith("00"):
        digits = "+" + digits[2:]
    elif digits.startswith("0"):
        digits = "+44" + digits[1:]
    return "tel:" + digits


def directory(iso: str, home: str | None = None) -> dict | None:
    """Everything a traveller needs to contact this country's representatives in the UK."""
    m = MISSIONS.get(iso)
    if not m:
        return None
    offices = []
    for o in m["consulates"] + m["honorary"]:
        city = clean_city(o["city"])
        km = _km(home, city) if home else None
        area = (o.get("area") or "").lower()
        covers = bool(home and any(w in area for w in REGION_WORDS.get(home, [])) and w_not_generic(area, home))
        offices.append({**o, "city": city, "km": round(km) if km is not None else None, "covers_you": covers})
    if home:
        dist = lambda o: o["km"] if o["km"] is not None else 9999  # noqa: E731  (0 km must not read as "unknown")
        offices.sort(key=lambda o: (o["status"] is not None, not o["covers_you"] and dist(o) > 40,
                                    o["kind"] != "consulate", dist(o)))
    else:
        offices.sort(key=lambda o: (o["status"] is not None, o["kind"] != "consulate", o["city"]))
    return {"embassy": m["embassy"], "consular": m["consular"], "offices": offices,
            "non_resident_in": m.get("non_resident_in"), "closed": m.get("closed", False)}


def w_not_generic(area: str, home: str) -> bool:
    """'England' alone shouldn't count as covering someone, unless nothing more specific exists."""
    specific = [w for w in REGION_WORDS.get(home, []) if w != "england"]
    return any(w in area for w in specific) or area.strip() in ("england", "england and wales", "the uk", "uk")


def nearest_office(iso: str, home: str | None) -> dict | None:
    """The single most useful office for someone living in `home` (None = embassy)."""
    d = directory(iso, home)
    if not d or not home:
        return None
    for o in d["offices"]:
        near = o["km"] is not None and o["km"] <= 40
        if o["status"] is None and o["kind"] == "consulate" and (o["covers_you"] or near):
            return o
    return None


def best_visa_contact(iso: str) -> dict | None:
    """The single office most likely to handle a visa question: a visa/consular section with
    real contact details, otherwise the embassy."""
    d = directory(iso)
    if not d:
        return None
    score = lambda r: (bool(re.search(r"visa", r["name"], re.I))  # noqa: E731
                       + bool(re.search(r"visa|consular|immigration|home affairs", r["name"], re.I)) * 2
                       + bool(r.get("phone")) + bool(r.get("email")) + bool(r.get("address")))
    candidates = [r for r in d["consular"] if r.get("phone") or r.get("email")]
    best = max(candidates, key=score) if candidates else d["embassy"]
    if best is None:
        return None
    if best is not d["embassy"] and d["embassy"]:
        # fill gaps from the embassy record (e.g. a section with an email but no address)
        best = {**best, "address": best.get("address") or d["embassy"].get("address"),
                "name": f"{d['embassy']['name']} — {best['name']}"}
    return {**best, "non_resident_in": d["non_resident_in"]}


def lists_age_days(today=None) -> int | None:
    """How old the FCDO lists are, from their 'Revised <Month Year>' heading."""
    from datetime import date, datetime
    try:
        revised = datetime.strptime(META["revised"], "%B %Y").date()
    except (ValueError, KeyError):
        return None
    return ((today or date.today()) - revised).days
