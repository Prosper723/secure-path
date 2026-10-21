"""
Secure Path — AI travel adviser.

Architecture (agentic, grounded):
  1. UNDERSTAND  parse() pulls structured slots out of free text: destination,
                 country of nationality, purpose, length, document type.
  2. REMEMBER    slots are merged into a per-conversation TripState, never
                 re-scraped from chat history (this caused wrong-country answers before).
  3. DECIDE      the same rules engine as the Trip Checker produces the verdict.
  4. EXPLAIN     demo mode writes the reply from templates; live mode asks an
                 LLM to explain the engine's verdict (it cannot change it).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Optional

from data import COUNTRIES, PURPOSES, FAQ, AI_LEGAL_CONTEXT, STATUS, CONFIDENCE
from engine import Trip, Assessment, assess

# ── Country index (longest names first so "South Sudan" beats "Sudan") ─────
_INDEX: list[tuple[str, str]] = []
for _c in COUNTRIES.values():
    for _n in {_c["name"].lower(), *_c["aliases"]}:
        _INDEX.append((_n, _c["iso2"]))
_INDEX += [("congo", "CD"), ("guinea", "GN"), ("micronesia", "FM")]
_INDEX.sort(key=lambda x: -len(x[0]))
_DEMONYMS = sorted(((d, c["iso2"]) for c in COUNTRIES.values() for d in c["demonyms"]), key=lambda x: -len(x[0]))

_ORIGIN_CUES = re.compile(
    r"(i'?m from|i am from|we are from|we're from|originally from|come from|came from|fled( from)?|"
    r"born in|citizen of|national of|nationality( is)?|my (home )?country( is)?|refugee from)\s*(the\s+)?$")

_NUM = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
        "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "couple of": 2, "few": 3}
_UNIT = {"day": 1, "night": 1, "week": 7, "month": 30, "year": 365}


def _find_countries(text: str) -> list[tuple[int, str]]:
    """Return (position, iso2) for every country mentioned, with word boundaries and no overlaps."""
    taken = [False] * len(text)
    hits = []
    for name, iso in _INDEX:
        for m in re.finditer(r"(?<![\w])" + re.escape(name) + r"(?![\w])", text):
            if not any(taken[m.start():m.end()]):
                hits.append((m.start(), iso))
                for i in range(m.start(), m.end()):
                    taken[i] = True
    return sorted(hits)


def parse(message: str) -> dict:
    t = " " + message.lower().replace("’", "'") + " "
    out: dict = {}

    # Countries: split into origin vs destination using the words just before each mention
    dests, origins = [], []
    for pos, iso in _find_countries(t):
        before = t[max(0, pos - 30):pos].strip()
        (origins if _ORIGIN_CUES.search(before) else dests).append(iso)
    for dem, iso in _DEMONYMS:
        if re.search(rf"\b(i'?m|i am|we are|as)\s+(an?\s+)?{re.escape(dem)}\b|\b{re.escape(dem)}\s+(refugee|national|citizen)\b", t):
            origins.append(iso)
            break
    # (a country can be both — e.g. "I'm from Eritrea, can I visit Eritrea?" — the engine handles that)
    non_uk = [d for d in dests if d != "GB"]
    if non_uk:
        out["destination"] = non_uk[0]
    elif "GB" in dests and not re.search(r"\b(from|in|live in|living in)\s+(the\s+)?(uk|england|britain)", t):
        out["destination"] = "GB"
    if origins:
        out["origin"] = origins[0]

    # Purpose — order matters: "unpaid" must win over "paid"/"work"
    rules = [
        ("transit", r"\b(transit|layover|stopover|connecting flight|change planes)\b"),
        ("volunteer", r"\b(unpaid|volunteer\w*|voluntary|charity work|not paid)\b"),
        ("paid_work", r"\b(paid|job|salary|employ\w*|internship|stipend|contract|work(ing)?\b(?! trip))"),
        ("study", r"\b(stud(y|ying)|universit\w*|course|masters|phd|degree|semester|exchange)\b"),
        ("business", r"\b(conference|business|meeting|work trip|summit|trade fair)\b"),
        ("medical", r"\b(medical|treatment|hospital|surgery|operation)\b"),
        ("family", r"\b(family|friends?|relatives?|wedding|funeral|mum|mom|dad|brother|sister|cousin|aunt|uncle|wife|husband|partner)\b"),
        ("tourism", r"\b(holiday|vacation|tourism|tourist|sightseeing|beach|city break|honeymoon|trip)\b"),
    ]
    for key, pattern in rules:
        if re.search(pattern, t):
            out["purpose"] = key
            break

    # Length of stay
    m = re.search(r"\b(\d{1,4}|an?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|couple of|few)\s*"
                  r"(day|night|week|month|year)s?\b", t)
    if m:
        n = m.group(1)
        out["days"] = (int(n) if n.isdigit() else _NUM[n]) * _UNIT[m.group(2)]
    elif "fortnight" in t:
        out["days"] = 14
    elif "weekend" in t:
        out["days"] = 3

    # Document type
    if "certificate of travel" in t:
        out["doc_type"] = "cot"
    elif "stateless" in t:
        out["doc_type"] = "stateless"
    return out


def faq_intent(message: str) -> Optional[str]:
    t = message.lower()
    checks = [
        ("esta", r"\besta\b|visa waiver"),
        ("ets31", r"\bets\b|ets ?(no\.? ?)?31|strasbourg|1959 agreement|abolition of visas"),
        ("schengen", r"90 ?/ ?180|schengen rule|how many days.*(schengen|europe)|\bees\b|entry.?exit"),
        ("evisa_uk", r"\b(ukvi|brp|uk evisa|my evisa|view and prove)\b"),
        ("validity", r"\b(expir\w*|valid for|validity|how long.*valid)\b"),
        ("origin", r"\b(go(ing)? (back )?home|go back to my country|visit my (home )?country|return to my country)\b"),
        ("ctd", r"what('?s| is) (a |the )?(ctd|convention travel|refugee travel|blue (travel )?document)"),
    ]
    for key, pattern in checks:
        if re.search(pattern, t):
            return key
    return None


# ── Conversation state ──────────────────────────────────────────────────────
@dataclass
class TripState:
    destination: Optional[str] = None
    origin: Optional[str] = None
    purpose: Optional[str] = None
    days: Optional[int] = None
    doc_type: str = "ctd"
    asked_purpose: bool = False
    carried: list = field(default_factory=list)   # slots reused from earlier turns (shown to the user)

    def merge(self, slots: dict, follow_up: bool) -> None:
        new_dest = slots.get("destination")
        self.carried = []
        if new_dest and self.destination and new_dest != self.destination:
            self.asked_purpose = False
            if follow_up:   # "what about Italy?" — same trip, different country: reuse and say so
                self.carried = [k for k in ("purpose", "days") if getattr(self, k) and k not in slots]
            else:           # a brand-new question — don't let the old trip leak into it
                self.purpose, self.days = None, None
        for k, v in slots.items():
            setattr(self, k, v)


@dataclass
class Reply:
    text: str
    assessment: Optional[Assessment] = None
    mode: str = "demo"


FOLLOW_UP = re.compile(r"^\s*(what about|how about|and|or|instead|same|what if)\b|^\W*(\w+\W*){1,4}$", re.I)
GREETING = re.compile(r"^\s*(hi|hello|hey|hiya|good (morning|afternoon|evening)|what can you do|help)\W*\s*$", re.I)
RESET = re.compile(r"\b(start over|reset|new trip|clear)\b", re.I)


def _icon(verdict: str) -> str:
    return {"go": "✅", "check": "🟠", "evisa": "🔵", "visa": "🔴", "stop": "⛔", "home": "🏠"}[verdict]


def _demo_text(a: Assessment, state: TripState, assumed_days: bool) -> str:
    c = a.country
    lines = [f"{_icon(a.verdict)} **{a.headline}** — {c['flag']} {c['name']}", "", a.summary]
    if a.actions:
        lines += ["", "**Next steps**"] + [f"{i}. {x}" for i, x in enumerate(a.actions[:3], 1)]
    notes = []
    if a.confidence != "high":
        notes.append(f"{CONFIDENCE[a.confidence]['label']} — confirm with the embassy")
    if assumed_days:
        notes.append("I've assumed a short stay under 90 days — tell me if it's longer")
    if state.carried:
        bits = {"purpose": PURPOSES.get(state.purpose, "").lower(), "days": f"{state.days} days"}
        notes.append("Using what you told me earlier: " + ", ".join(bits[k] for k in state.carried))
    if notes:
        lines += ["", "_" + " · ".join(notes) + "_"]
    return "\n".join(lines)


def respond(message: str, state: TripState, history: list, api: Optional[dict] = None) -> Reply:
    """Main entry point. `api` = {"provider": "anthropic"|"openai", "key": str} for live mode."""
    if RESET.search(message):
        state.__init__()
        return Reply("Done — starting fresh. Where are you thinking of going?")

    if GREETING.match(message):
        return Reply("Hi! Tell me **where** you're going, **why**, and **for how long**, and I'll check the "
                     "rules for your UK travel document.\n\nFor example: *“Paid internship in Germany for 3 "
                     "months”* or *“Visiting my sister in Canada for 2 weeks”*.")

    slots = parse(message)
    intent = faq_intent(message)

    # Pure knowledge question (no trip details in this message)
    if intent and not slots.get("destination"):
        if intent == "origin" and state.origin:
            return Reply(FAQ["origin"])
        return Reply(FAQ[intent])

    state.merge(slots, follow_up=bool(FOLLOW_UP.search(message)))

    if not state.destination:
        return Reply("Which country are you planning to visit?"
                     + (" (You mentioned where you're from — I'll use that to check your document is valid there.)"
                        if state.origin else ""))

    # Agentic questioning: only ask about purpose when the answer depends on it.
    c = COUNTRIES[state.destination]
    long_stay = bool(state.days and state.days > c["max_stay_days"])
    purpose_changes_answer = c["status"] in ("visa_free", "check") and not long_stay and state.origin != state.destination
    purpose_assumed = False
    if not state.purpose:
        if purpose_changes_answer and not state.asked_purpose:
            state.asked_purpose = True
            return Reply(f"Got it — {c['flag']} **{c['name']}**. What's the trip for?\n\n"
                         "Holiday · visiting family · business meeting · study · unpaid volunteering · "
                         "**paid work or a paid internship**\n\n"
                         "_This changes the answer: paid work needs a work permit even where visits are visa-free._")
        purpose_assumed = True

    assumed_days = state.days is None
    trip = Trip(destination=state.destination, purpose=state.purpose or "tourism", days=state.days or 14,
                doc_type=state.doc_type, origin=state.origin)
    a = assess(trip)
    extra = ""
    if purpose_assumed and a.verdict in ("visa", "evisa"):
        extra = ("\n\n_" + (f"Whatever the purpose, {state.days} days is over the {c['max_stay_days']}-day limit, so "
                            "you need a long-stay visa. Tell me the purpose and I'll tell you which kind."
                            if long_stay else
                            "A visa is needed whatever the purpose. If it's paid work, you'll need a work visa "
                            "specifically.") + "_")

    if api and api.get("key"):
        try:
            return Reply(_live_text(message, history, a, assumed_days, api) + extra, a, mode="live")
        except Exception as e:  # never leave the user without an answer
            text = _demo_text(a, state, assumed_days) + extra
            return Reply(text + f"\n\n_Live AI unavailable ({type(e).__name__}) — showing the rules-engine answer._", a)
    return Reply(_demo_text(a, state, assumed_days) + extra, a)


# ── Live LLM ────────────────────────────────────────────────────────────────
def _live_text(message: str, history: list, a: Assessment, assumed_days: bool, api: dict) -> str:
    grounding = {
        "engine_result": a.to_dict(),
        "status_label": STATUS[a.country["status"]]["label"],
        "assumed_length": assumed_days,
        "reasoning_steps": [{"title": s.title, "detail": s.detail, "outcome": s.outcome} for s in a.steps],
    }
    user = f"{message}\n\n[SECURE PATH ENGINE RESULT — authoritative]\n{json.dumps(grounding, default=str)}"
    # Providers need alternating turns that start with the user: drop leading assistant
    # messages (the welcome note) and merge consecutive same-role messages.
    turns: list[dict] = []
    for m in history[-8:]:
        if m["role"] not in ("user", "assistant") or (not turns and m["role"] == "assistant"):
            continue
        if turns and turns[-1]["role"] == m["role"]:
            turns[-1]["content"] += "\n\n" + m["content"]
        else:
            turns.append({"role": m["role"], "content": m["content"]})
    if turns and turns[-1]["role"] == "user":
        turns.pop()  # the current message is sent separately with the engine grounding

    if api["provider"] == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=api["key"])
        r = client.messages.create(model=os.getenv("SECURE_PATH_ANTHROPIC_MODEL", "claude-haiku-4-5"),
                                   max_tokens=500, system=AI_LEGAL_CONTEXT,
                                   messages=turns + [{"role": "user", "content": user}])
        return r.content[0].text
    from openai import OpenAI
    client = OpenAI(api_key=api["key"])
    r = client.chat.completions.create(model=os.getenv("SECURE_PATH_OPENAI_MODEL", "gpt-4o-mini"),
                                       temperature=0.2, max_tokens=500,
                                       messages=[{"role": "system", "content": AI_LEGAL_CONTEXT}] + turns
                                       + [{"role": "user", "content": user}])
    return r.choices[0].message.content
