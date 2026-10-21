"""
Secure Path — trip assessment engine.

One function, assess(trip), turns a trip into an explainable decision:
a verdict, a headline, and the ordered reasoning steps that produced it
(each with an outcome and, where relevant, its legal source).

The Trip Checker, the AI adviser (demo and live) and the exports all use
this engine, so every part of the app gives the same answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date, timedelta
from typing import Optional

from data import (COUNTRIES, SOURCES, DOC_TYPES, PURPOSES, CHECKLIST_BASE, CHECKLIST_PURPOSE,
                  CHECKLIST_VISA, DATA_REVIEWED)

# Verdict severity: higher wins when rules combine.
SEVERITY = {"go": 0, "check": 1, "evisa": 2, "visa": 3, "stop": 4, "home": 5}
BASE_VERDICT = {"visa_free": "go", "check": "check", "evisa": "evisa", "visa_required": "visa", "issuer": "home"}

HEADLINES = {
    "go":    "Usually no visa needed for this trip",
    "check": "Confirm with the embassy before you book",
    "evisa": "You need a visa — you may be able to apply online",
    "visa":  "You need a visa before you travel",
    "stop":  "Don't travel on this plan",
    "home":  "This is where your document was issued",
}

LEAD_WEEKS = {"visa": 8, "evisa": 3, "check": 6}

# Country names that read naturally with "the" ("the embassy of the Netherlands")
_THE = {"US", "GB", "NL", "PH", "BS", "GM", "CZ", "CF", "DO", "CD", "CG", "AE", "MV", "MH", "SB", "KM", "SC"}


def country_name(c: dict) -> str:
    return ("the " if c["iso2"] in _THE else "") + c["name"]


def country_cap(c: dict) -> str:
    """Country name for the start of a sentence ("The Netherlands requires…")."""
    n = country_name(c)
    return n[0].upper() + n[1:]


def embassy_of(c: dict) -> str:
    return f"the embassy of {country_name(c)}"


def near_you(trip: "Trip") -> str:
    """Embassies are in London, but many countries also have consulates or visa centres elsewhere."""
    if trip.city and trip.city != "London":
        return f" (or its consulate or visa application centre near {trip.city}, if it has one)"
    return " or its consulate"


@dataclass
class Trip:
    destination: str                    # ISO2
    purpose: str = "tourism"            # key of PURPOSES
    days: int = 7
    doc_type: str = "ctd"               # key of DOC_TYPES
    origin: Optional[str] = None        # ISO2 — country of nationality / country fled
    depart: Optional[date] = None
    doc_expiry: Optional[date] = None
    city: Optional[str] = None          # nearest UK city, for consulates / visa centres

    @property
    def return_date(self) -> Optional[date]:
        return self.depart + timedelta(days=self.days) if self.depart else None


@dataclass
class Step:
    title: str
    detail: str
    outcome: str = "info"               # pass | warn | fail | info
    source: Optional[dict] = None


@dataclass
class Assessment:
    verdict: str
    headline: str
    summary: str
    confidence: str
    country: dict
    trip: Trip
    steps: list = field(default_factory=list)
    actions: list = field(default_factory=list)
    apply_by: Optional[date] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["trip"] = {k: (v.isoformat() if isinstance(v, date) else v) for k, v in d["trip"].items()}
        d["apply_by"] = self.apply_by.isoformat() if self.apply_by else None
        d["country"] = {k: self.country[k] for k in ("name", "iso2", "status", "confidence", "summary")}
        return d


def _escalate(current: str, new: str) -> str:
    return new if SEVERITY[new] > SEVERITY[current] else current


def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day, 28))


def assess(trip: Trip, today: Optional[date] = None) -> Assessment:
    today = today or date.today()
    c = COUNTRIES[trip.destination]
    doc = DOC_TYPES[trip.doc_type]
    steps: list[Step] = []
    actions: list[str] = []
    confidence = c["confidence"]
    purpose_label = PURPOSES[trip.purpose]

    # ── 0. Issuing country ────────────────────────────────────────────────
    if c["status"] == "issuer":
        steps.append(Step("Destination is the UK",
                          "Your document was issued by the UK, which guarantees your right to return.", "pass"))
        return Assessment("home", HEADLINES["home"], c["summary"], "high", c, trip, steps,
                          ["Choose a destination outside the UK."])

    verdict = BASE_VERDICT[c["status"]]

    # ── 1. Country of nationality ────────────────────────────────────────
    if trip.origin and trip.origin == trip.destination:
        if trip.doc_type == "ctd":
            steps.append(Step(
                "Your country of nationality",
                f"A Convention Travel Document is not valid for {c['name']}. Going back, or getting that "
                "country's passport, can lead to your refugee status being reviewed (1951 Convention, Art. 1C).",
                "fail"))
            actions = ["Don't book this trip on your CTD.",
                       "Speak to an immigration solicitor or a refugee advice charity before considering it."]
            return Assessment("stop", "Your CTD isn't valid for this country",
                              "Refugee travel documents exclude your country of nationality. Travelling there "
                              "could put your protection status at risk.", "high", c, trip, steps, actions)
        steps.append(Step("Your former country", f"Check carefully whether {c['name']} will admit you on this "
                          "document — get legal advice first.", "warn"))
    elif trip.origin:
        steps.append(Step("Country of nationality",
                          f"Your destination isn't your country of nationality, so your document can be used.", "pass"))

    # ── 2. Destination's general rule for this document ─────────────────
    status_text = c["summary"]
    if trip.doc_type == "cot":
        if verdict in ("go", "check"):
            verdict = "visa"
            confidence = "medium"
        status_text = (f"Certificate of Travel holders aren't covered by the refugee/stateless exemptions "
                       f"that some UK document holders get, and some countries don't accept the document at all. "
                       f"Plan on needing a visa for {c['name']}, and check that it recognises your document.")
        steps.append(Step(f"Entry rule for {c['name']}", status_text, "warn"))
    else:
        outcome = {"go": "pass", "check": "warn", "evisa": "warn", "visa": "fail"}[verdict]
        src = c["sources"][0] if c["sources"] else None
        steps.append(Step(f"Entry rule for {c['name']}", status_text, outcome, src))

    if c["schengen"]:
        steps.append(Step("Schengen area",
                          "Short stays are capped at 90 days in any 180-day period across ALL Schengen countries "
                          "combined. Your fingerprints and photo are recorded at the border (EU Entry/Exit System).",
                          "info", SOURCES["ees"]))
    if c["ets31"] != "none":
        note = f", but {c['ets31_note']}" if c["ets31_note"] else ""
        steps.append(Step("ETS No. 31 (1959 refugee visa agreement)",
                          f"{country_cap(c)} is a party to ETS No. 31{note}. "
                          "However, the UK suspended the agreement in 2003, "
                          "and under Art. 7(2) UK-issued documents can't claim its benefits, so it doesn't decide "
                          "your entry.", "info", SOURCES["ets_text"]))

    # ── 3. Purpose of the trip ───────────────────────────────────────────
    p = trip.purpose
    if p == "paid_work":
        verdict = _escalate(verdict, "visa")
        confidence = "high" if c["status"] != "check" else confidence
        steps.append(Step("Purpose: paid work",
                          "Paid work, including a paid internship or stipend, needs work authorisation (a work "
                          "visa or permit) in every country, even where visits are visa-free.", "fail"))
        actions.append("Ask your employer what work visa or permit they will sponsor — start 3 months ahead.")
    elif p == "study":
        if trip.days > 90:
            verdict = _escalate(verdict, "visa")
            steps.append(Step("Purpose: study over 90 days", "Courses over 90 days need a student visa.", "fail"))
        else:
            steps.append(Step("Purpose: short course",
                              "Short courses of up to 90 days are often allowed as a visitor, but ask the "
                              "institution to confirm in writing.", "warn"))
    elif p == "volunteer":
        steps.append(Step("Purpose: unpaid volunteering",
                          "Usually allowed on a visit, but some countries treat structured volunteering (with "
                          "free accommodation or expenses) as work. Get the unpaid status in writing.", "warn"))
    elif p == "business":
        steps.append(Step("Purpose: business visit",
                          "Meetings and conferences are normally allowed on a visit. Doing paid work for a local "
                          "client is not.", "pass" if verdict == "go" else "info"))
    elif p == "transit":
        if trip.destination in ("US", "CA"):
            verdict = _escalate(verdict, "visa")
            steps.append(Step("Transit", f"{country_cap(c)} requires a visa even to change planes.", "fail"))
        else:
            steps.append(Step("Transit",
                              "Airport transit rules depend on the airport and your document. Ask the airline "
                              "before you book, as they can deny boarding.", "warn"))
    elif p == "medical":
        steps.append(Step("Purpose: medical treatment",
                          "Carry the hospital's letter and proof you can pay. Longer treatment may need a "
                          "medical visa.", "info"))
    else:
        steps.append(Step(f"Purpose: {purpose_label.lower()}", "A standard visit purpose.", "pass"))

    # ── 4. Length of stay ────────────────────────────────────────────────
    if trip.days > c["max_stay_days"] and p != "transit":
        verdict = _escalate(verdict, "visa")
        steps.append(Step("Length of stay",
                          f"{trip.days} days is over the {c['max_stay_days']}-day short-stay limit, so you need a "
                          "long-stay (national) visa or residence permit.", "fail"))
    else:
        steps.append(Step("Length of stay", f"{trip.days} days is within the short-stay limit.", "pass"))
    if trip.days > 730:
        steps.append(Step("Time outside the UK",
                          "If you have indefinite leave to remain, it can lapse after more than 2 years outside "
                          "the UK.", "warn"))

    # ── 5. Document validity ─────────────────────────────────────────────
    if trip.doc_expiry and trip.depart:
        ret = trip.return_date
        need = _add_months(ret, c["validity_months"])
        if trip.doc_expiry <= ret:
            verdict = "stop"
            steps.append(Step("Document validity",
                              f"Your document expires on {trip.doc_expiry:%d %b %Y}, before you return on "
                              f"{ret:%d %b %Y}.", "fail"))
            actions.insert(0, "Renew your travel document first — the Home Office can take several weeks.")
        elif trip.doc_expiry < need:
            hard = c["schengen"]
            if hard:
                verdict = "stop"
            steps.append(Step("Document validity",
                              f"{country_cap(c)} expects about {c['validity_months']} months of validity after you "
                              f"leave (until {need:%d %b %Y}). Yours expires {trip.doc_expiry:%d %b %Y}.",
                              "fail" if hard else "warn"))
            actions.insert(0, "Renew your travel document before you travel, or check with the airline.")
        else:
            steps.append(Step("Document validity",
                              f"Valid until {trip.doc_expiry:%d %b %Y} — enough for this trip.", "pass"))
    else:
        steps.append(Step("Document validity",
                          f"Add your expiry date to check it. {country_cap(c)} expects about {c['validity_months']} "
                          "months of validity after you leave.", "info"))

    # ── 6. Timing ────────────────────────────────────────────────────────
    apply_by = None
    if trip.depart and verdict in LEAD_WEEKS:
        weeks = 12 if trip.destination == "US" else LEAD_WEEKS[verdict]
        apply_by = trip.depart - timedelta(weeks=weeks)
        late = apply_by < today
        steps.append(Step("Timing",
                          (f"Apply by {apply_by:%d %b %Y} (about {weeks} weeks before departure)."
                           + (" That date has passed — consider moving your travel date." if late else "")),
                          "warn" if late else "info"))

    # ── 7. Safety ────────────────────────────────────────────────────────
    if c["fcdo_warning"]:
        steps.append(Step("Travel safety",
                          f"The UK Foreign Office advises against all or some travel to parts of {c['name']}. "
                          "Check the latest advice, as your insurance may not cover you.", "warn",
                          {"label": "FCDO travel advice", "url": "https://www.gov.uk/foreign-travel-advice"}))

    # ── 8. Leaving and returning to the UK ───────────────────────────────
    steps.append(Step("Your UK status",
                      "Make sure your UKVI eVisa account shows this travel document. Airlines and UK Border "
                      "Force check it when you come back.", "info"))

    # ── Actions ──────────────────────────────────────────────────────────
    if verdict == "go":
        if confidence != "high":
            actions.append(f"Email {embassy_of(c)}{near_you(trip)} to confirm — use the letter template below.")
        actions.append("Collect the documents in your checklist.")
    elif verdict == "check":
        actions.append(f"Before booking anything, ask {embassy_of(c)}{near_you(trip)} in writing.")
    elif verdict == "evisa":
        if c.get("evisa_url"):
            actions.append(f"Check the official online system accepts a {doc['short'].split(' (')[0].lower()}: "
                           f"{c['evisa_url']}")
        actions.append(f"If it doesn't, apply through {embassy_of(c)}{near_you(trip)}.")
    elif verdict == "visa" and p != "paid_work":
        actions.append(f"Book a visa appointment with {embassy_of(c)}{near_you(trip) if trip.city and trip.city != 'London' else ' or its visa application centre'}.")
    if verdict in ("check", "visa", "evisa"):
        actions.append("Don't pay for non-refundable flights until your entry is confirmed.")

    headline = HEADLINES[verdict]
    if verdict == "stop" and any(s.title == "Document validity" and s.outcome == "fail" for s in steps):
        headline = "Renew your travel document first"
    if verdict == "go" and confidence == "high":
        headline = "No visa needed for this trip"

    summary = {
        "go": f"Short {purpose_label.lower()} trips to {country_name(c)} are usually visa-free with your document.",
        "check": f"We can't confirm {c['name']}'s current rule for your document. Get written confirmation first.",
        "evisa": f"{country_cap(c)} requires a visa. An online system exists, but check it accepts your document.",
        "visa": f"Apply to {embassy_of(c)} before you travel.",
        "stop": "There's a problem with this trip that needs fixing before you go.",
    }[verdict]
    if p == "paid_work" and verdict == "visa":
        summary = f"Paid work in {country_name(c)} needs a work visa or permit, issued before you start."

    return Assessment(verdict, headline, summary, confidence, c, trip, steps,
                      [a for a in actions if a], apply_by)


# ── Checklist & journey ─────────────────────────────────────────────────────
def checklist(a: Assessment) -> list[str]:
    items = list(CHECKLIST_BASE) + CHECKLIST_PURPOSE.get(a.trip.purpose, [])
    if a.verdict in ("visa", "evisa"):
        items += CHECKLIST_VISA
    if a.trip.destination == "US":
        items += ["DS-160 online form and interview booking confirmation"]
    if a.country["schengen"]:
        items += ["Check whether you need ETIAS travel authorisation (EU scheme due to start in late 2026)"]
    if a.trip.doc_type == "cot":
        items += ["Written confirmation that the destination accepts a Certificate of Travel"]
    # de-duplicate while keeping order
    seen, out = set(), []
    for i in items:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def journey(a: Assessment) -> list[dict]:
    d = a.trip.depart
    fmt = lambda days: (d - timedelta(days=days)).strftime("%d %b %Y") if d else None  # noqa: E731
    steps = [{"title": "Check entry rules", "when": "Done", "detail": "You've assessed this trip with Secure Path."}]
    if a.verdict in ("check",) or a.confidence != "high":
        steps.append({"title": "Confirm with the embassy", "when": fmt(70) or "~10 weeks before",
                      "detail": "Send the enquiry letter and keep the reply. Bring it with you."})
    if a.verdict in ("visa", "evisa"):
        weeks = 12 if a.trip.destination == "US" else LEAD_WEEKS[a.verdict]
        steps.append({"title": "Apply for your visa", "when": fmt(weeks * 7) or f"~{weeks} weeks before",
                      "detail": "Apply online or book the embassy appointment. Track it weekly."})
    steps += [
        {"title": "Gather documents", "when": fmt(21) or "~3 weeks before",
         "detail": "Work through your checklist. Keep paper copies and photos on your phone."},
        {"title": "Book and insure", "when": fmt(14) or "Once entry is confirmed",
         "detail": "Book flights once entry is confirmed, and get insurance that covers the trip purpose."},
        {"title": "Update your UKVI account", "when": fmt(7) or "1 week before",
         "detail": "Check your eVisa shows your current travel document."},
        {"title": "At the border", "when": d.strftime("%d %b %Y") if d else "Travel day",
         "detail": "Show your document, plus your visa or confirmation letter. Stay calm and answer clearly."},
        {"title": "Return to the UK", "when": a.trip.return_date.strftime("%d %b %Y") if d else "Return day",
         "detail": "Use the staffed desks if the eGates don't accept your document."},
    ]
    return steps


# ── Exports ─────────────────────────────────────────────────────────────────
def trip_summary_md(a: Assessment) -> str:
    t, c = a.trip, a.country
    lines = [f"# Secure Path — trip assessment", "",
             f"**Destination:** {c['name']}  ",
             f"**Purpose:** {PURPOSES[t.purpose]}  ",
             f"**Length:** {t.days} days" + (f" (from {t.depart:%d %b %Y})" if t.depart else "") + "  ",
             f"**Document:** {DOC_TYPES[t.doc_type]['name']}", "",
             f"## Result: {a.headline}", "", a.summary, "",
             f"Confidence: {a.confidence} · Data reviewed {DATA_REVIEWED}", "", "## How this was decided", ""]
    icon = {"pass": "✓", "warn": "!", "fail": "✕", "info": "·"}
    for s in a.steps:
        lines.append(f"- {icon[s.outcome]} **{s.title}** — {s.detail}")
    lines += ["", "## What to do next", ""] + [f"{i}. {x}" for i, x in enumerate(a.actions, 1)]
    lines += ["", "## Checklist", ""] + [f"- [ ] {x}" for x in checklist(a)]
    lines += ["", "## Sources", ""] + [f"- {s['label']}: {s['url']}" for s in c["sources"]]
    lines += ["", "_Guidance only — not legal advice. Always confirm with the embassy before travelling._"]
    return "\n".join(lines)


def embassy_letter(a: Assessment, name: str = "[Your name]") -> str:
    t, c = a.trip, a.country
    doc = DOC_TYPES[t.doc_type]
    when = f"from {t.depart:%d %B %Y} for {t.days} days" if t.depart else f"for about {t.days} days"
    schengen_line = (
        "\nI understand that, under Article 6(2) of Regulation (EU) 2018/1806, Member States may exempt "
        "refugees and stateless persons residing in the United Kingdom from the visa requirement, and I would "
        "be grateful if you could confirm whether this exemption applies to me.\n"
        if c["schengen"] and t.doc_type != "cot" else "")
    return f"""Subject: Visa requirement enquiry — holder of a UK {doc['name']}

Dear Consular Section, Embassy of {country_name(c)},

I hold a {doc['name']} issued by the UK Home Office ({doc['basis']}). I live in the United Kingdom and have valid permission to stay.

I am planning to travel to {c['name']} {when}. The purpose of my trip is: {PURPOSES[t.purpose].lower()}.

Could you please confirm in writing:
1. Whether I need a visa for this trip, and if so which type;
2. Whether your country accepts my travel document for entry;
3. Any minimum validity your country requires for my document.
{schengen_line}
I would be grateful for a written reply that I can show to my airline and at the border.

Kind regards,
{name}
"""
