"""Secure Path test suite — run with:  python -m pytest -q"""

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data import COUNTRIES  # noqa: E402
from engine import Trip, assess, checklist, journey, trip_summary_md, embassy_letter  # noqa: E402
from adviser import parse, TripState, respond  # noqa: E402

TODAY = date(2026, 10, 21)


# ── Data integrity ──────────────────────────────────────────────────────────
def test_world_coverage():
    assert len(COUNTRIES) >= 195


def test_every_country_has_status_confidence_and_source():
    for c in COUNTRIES.values():
        assert c["status"] in {"visa_free", "evisa", "visa_required", "check", "issuer"}, c["name"]
        assert c["confidence"] in {"verified", "high", "medium", "low"}, c["name"]
        assert c["sources"], c["name"]
        assert c["summary"], c["name"]


def test_corrected_legal_facts():
    assert COUNTRIES["GB"]["ets31"] == "suspended"
    assert COUNTRIES["FR"]["ets31"] == "suspended"
    assert COUNTRIES["IE"]["status"] == "visa_required"
    for not_party in ("AT", "GR", "TR"):           # wrongly listed as ETS 31 parties in v2
        assert COUNTRIES[not_party]["ets31"] == "none"


def test_nothing_low_confidence_is_marked_safe_without_caveat():
    for c in COUNTRIES.values():
        if c["status"] == "visa_free" and c["confidence"] == "low":
            assert "confirm" in c["summary"].lower() or "usually" in c["summary"].lower(), c["name"]


# ── Engine ──────────────────────────────────────────────────────────────────
def run(dest, purpose="tourism", days=10, **kw):
    return assess(Trip(destination=dest, purpose=purpose, days=days, **kw), today=TODAY)


def test_paid_work_needs_visa_even_where_visits_are_visa_free():
    a = run("RO", "paid_work", 90)
    assert a.verdict == "visa"
    assert any(s.title == "Purpose: paid work" and s.outcome == "fail" for s in a.steps)


def test_holiday_in_visa_free_schengen_state():
    assert run("DE").verdict == "go"


def test_over_90_days_needs_long_stay_visa():
    assert run("DE", days=120).verdict == "visa"


def test_country_of_nationality_blocks_ctd():
    a = run("ER", origin="ER")
    assert a.verdict == "stop" and a.confidence == "high"


def test_stateless_document_not_blocked_for_former_country():
    assert run("ER", origin="ER", doc_type="stateless").verdict != "stop"


def test_certificate_of_travel_never_visa_free():
    assert run("DE", doc_type="cot").verdict == "visa"


def test_usa_requires_visa_including_transit():
    assert run("US").verdict == "visa"
    assert run("US", "transit", 1).verdict == "visa"


def test_document_expiring_before_return_stops_trip():
    a = run("ES", depart=TODAY + timedelta(days=30), doc_expiry=TODAY + timedelta(days=35))
    assert a.verdict == "stop" and a.headline == "Renew your travel document first"


def test_schengen_three_month_validity_rule():
    a = run("DE", depart=TODAY + timedelta(days=30), doc_expiry=TODAY + timedelta(days=80))
    assert a.verdict == "stop"
    ok = run("DE", depart=TODAY + timedelta(days=30), doc_expiry=TODAY + timedelta(days=400))
    assert ok.verdict == "go"


def test_late_visa_application_is_flagged():
    a = run("US", depart=TODAY + timedelta(days=20))
    assert any(s.title == "Timing" and s.outcome == "warn" for s in a.steps)


def test_uk_is_home():
    assert run("GB").verdict == "home"


def test_every_destination_assesses_without_error():
    for iso in COUNTRIES:
        for p in ("tourism", "paid_work", "study", "transit"):
            a = run(iso, p, 30, depart=TODAY + timedelta(days=60), doc_expiry=TODAY + timedelta(days=900))
            assert a.headline and a.steps
            assert checklist(a) and journey(a)
            assert trip_summary_md(a) and embassy_letter(a)


# ── Language understanding & conversation memory ────────────────────────────
def test_parse_basics():
    assert parse("paid internship in Germany for 3 months") == {"destination": "DE", "purpose": "paid_work", "days": 90}
    assert parse("unpaid volunteering in Kenya for six weeks")["purpose"] == "volunteer"
    assert parse("going to papua new guinea")["destination"] == "PG"
    assert parse("going to Nigeria")["destination"] == "NG"
    assert parse("trip to Niger")["destination"] == "NE"
    assert parse("work trip to dubai") == {"destination": "AE", "purpose": "business"}


def test_parse_origin_vs_destination():
    p = parse("I fled Syria and want a holiday in Turkey for 2 weeks")
    assert p["origin"] == "SY" and p["destination"] == "TR"
    p = parse("I'm from Eritrea, can I go to Eritrea to see my mum")
    assert p["origin"] == "ER" and p["destination"] == "ER"


def test_regression_egypt_not_france():
    """v2 bug: previous assistant text mentioning France hijacked an Egypt question."""
    state = TripState()
    hist = []
    for msg in ("travelling to spain for 6 months", "im going egypt do i need a visa"):
        r = respond(msg, state, hist)
        hist += [{"role": "user", "content": msg}, {"role": "assistant", "content": r.text}]
    assert state.destination == "EG"
    assert "Egypt" in r.text and "France" not in r.text
    assert "180 days" not in r.text          # the Spain trip's length must not leak into a new question


def test_regression_help_does_not_hijack_question():
    r = respond("travelling to spain for 6 months help", TripState(), [])
    assert "Spain" in r.text


def test_follow_up_keeps_context():
    s = TripState()
    respond("paid internship in Romania for 3 months", s, [])
    r = respond("what about the netherlands?", s, [])
    assert s.destination == "NL" and s.purpose == "paid_work"
    assert "earlier" in r.text


def test_asks_purpose_only_when_it_changes_the_answer():
    s = TripState()
    r1 = respond("I'm going to Germany", s, [])          # visa-free country: paid work would change it
    assert "What's the trip for" in r1.text
    r2 = respond("for a few days", s, [])
    assert r2.assessment is not None
    r3 = respond("I'm going to Japan", TripState(), [])   # visa needed anyway: answer straight away
    assert r3.assessment is not None and "whatever the purpose" in r3.text
    r4 = respond("travelling to spain for 6 months", TripState(), [])  # over 90 days: answer straight away
    assert r4.assessment.verdict == "visa" and "long-stay" in r4.text


def test_faq_and_reset():
    assert "ESTA" in respond("can I use esta?", TripState(), []).text
    s = TripState(destination="DE")
    respond("start over", s, [])
    assert s.destination is None


# ── Evidence policy (v3.1): visa-free only with official, quoted, dated evidence ─
def test_visa_free_requires_official_evidence():
    for c in COUNTRIES.values():
        if c["status"] == "visa_free":
            assert c["confidence"] == "verified" or c["iso2"] in {"SM", "VA"}, c["name"]


def test_verified_entries_have_quote_url_and_date():
    verified = [c for c in COUNTRIES.values() if c["confidence"] == "verified"]
    assert {c["iso2"] for c in verified} >= {"DE", "IT", "CH", "BE", "ES"}
    for c in verified:
        ev = c["evidence"]
        assert ev["quote"] and ev["source"]["url"].startswith("https://") and ev["checked"]
        assert set(c["by_doc"]) == {"ctd", "stateless", "cot"}


def test_embassy_verified_outcomes_by_document():
    assert run("DE").verdict == "go" and run("DE").confidence == "verified"
    assert run("DE", doc_type="cot").verdict == "visa"      # German page: black document needs a visa
    assert run("BE").verdict == "visa"                       # Belgian embassy: blue document needs a Schengen visa
    assert run("ES", doc_type="stateless").verdict == "visa"
    assert run("NL").verdict == "check"                      # not confirmed by an embassy → never visa-free


def test_stale_evidence_falls_back_to_check():
    a = assess(Trip(destination="DE", purpose="tourism", days=10), today=date(2027, 9, 1))
    assert a.verdict == "check"


def test_onward_travel_warning_for_national_exemptions():
    assert any(s.title == "Travelling on to other countries" for s in run("IT").steps)


# ── Embassy & consulate directory (FCDO lists, Oct 2026) ────────────────────
import re  # noqa: E402
from contacts import MISSIONS, directory, nearest_office, best_visa_contact  # noqa: E402


def _all_records():
    for iso, m in MISSIONS.items():
        for r in ([m["embassy"]] if m["embassy"] else []) + m["consular"] + m["consulates"] + m["honorary"]:
            yield iso, r


def test_directory_covers_almost_every_country():
    assert len(MISSIONS) >= 185
    assert sum(1 for m in MISSIONS.values() if m["embassy"]) >= 180


def test_no_personal_names_in_contact_data():
    """Diplomats' names are personal data and are never stored — only office details."""
    person = re.compile(r"\b(Mr|Mrs|Ms|Miss|Dr|Excellency|Princess|Prince(?![’']s Gate| Consort)|Earl|Alderman|Revd|Honorary Consul\b)\b"
                        r"|\b[A-Z]{3,} [A-Z]{3,} [A-Z]{3,}\b")
    for iso, r in _all_records():
        assert not person.search(r["address"]), (iso, r["address"])


def test_addresses_do_not_contain_phone_numbers_or_emails():
    for iso, r in _all_records():
        assert "@" not in r["address"], (iso, r["address"])
        assert not re.search(r"\b0\d{3} ?\d{3} ?\d{4}\b", r["address"]), (iso, r["address"])


def test_known_offices():
    es = directory("ES", "Manchester")
    assert es["offices"][0]["city"] == "Manchester" and es["offices"][0]["kind"] == "consulate"
    assert nearest_office("PK", "Leeds")["city"] == "Bradford"
    assert "Visa" in best_visa_contact("EG")["name"]
    assert directory("AU")["embassy"]["name"] == "Australian High Commission"   # not overwritten by Agents General
    assert directory("AD")["non_resident_in"] == "Andorra"


def test_trip_actions_name_the_real_consulate():
    a = assess(Trip(destination="ES", purpose="tourism", days=10, city="Manchester"), today=TODAY)
    assert "consulate in Manchester" in a.actions[0]
    a = assess(Trip(destination="EG", purpose="tourism", days=10), today=TODAY)
    assert all("consulates" not in x for x in a.actions)   # Egypt has none outside London
