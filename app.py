"""
Secure Path — GovTech prototype
Visa answers for people travelling on UK Home Office travel documents.

Run:  python -m streamlit run app.py
"""

import os
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from data import (COUNTRIES, DESTINATIONS, PURPOSES, DOC_TYPES, STATUS, CONFIDENCE, SOURCES, FAQ,
                  DATA_REVIEWED)
from engine import Trip, assess, checklist, journey, trip_summary_md, embassy_letter, country_name
from contacts import directory, nearest_office, UK_CITIES, META as CONTACTS_META, lists_age_days
from adviser import TripState, respond
import ui

st.set_page_config(page_title="Secure Path — visa checker for UK travel document holders",
                   page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")
ui.inject_css()
ui.header()

TODAY = date.today()
DEST_CODES = [c["iso2"] for c in DESTINATIONS]
ALL_CODES = sorted(COUNTRIES, key=lambda k: COUNTRIES[k]["name"])
label = lambda iso: f"{COUNTRIES[iso]['flag']}  {COUNTRIES[iso]['name']}"  # noqa: E731

# ── Session defaults ────────────────────────────────────────────────────────
for k, v in {"dest": None, "purpose": "tourism", "depart": TODAY + timedelta(days=45),
             "ret": TODAY + timedelta(days=59), "doc": "ctd", "origin": None, "expiry": None, "city": None,
             "chat": [], "trip_state": TripState(), "api_key": "", "provider": "anthropic"}.items():
    st.session_state.setdefault(k, v)


def quick_start(dest, purpose, days):
    st.session_state.update(dest=dest, purpose=purpose, depart=TODAY + timedelta(days=45),
                            ret=TODAY + timedelta(days=45 + days))


def render_directory(iso: str, home: str | None):
    """Embassy, visa/consular sections and offices near the user — from the FCDO lists."""
    d = directory(iso, home)
    c = COUNTRIES[iso]
    if not d:
        ui.callout("No office listed in the UK",
                   f"The FCDO lists don't show an embassy or consulate for {country_name(c)}. Its nearest embassy "
                   "is usually in another European capital — search the country's foreign ministry website.", "amber")
        return
    if d["closed"] or (d["embassy"] and d["embassy"].get("status")):
        ui.callout("Embassy temporarily closed",
                   "The FCDO list shows this embassy as closed. Contact a consulate below, or the country's "
                   "embassy in another European capital.", "amber")
    if d["non_resident_in"]:
        ui.callout(f"No embassy in the UK — covered from {d['non_resident_in']}",
                   f"{country_name(c)[0].upper() + country_name(c)[1:]}'s ambassador to the UK is based in "
                   f"{d['non_resident_in']}. Contact that embassy below, or an honorary consul in the UK if one is "
                   "listed.", "blue")
    if d["embassy"]:
        ui.contact_card(d["embassy"], "Embassy" if not d["non_resident_in"] else f"Embassy (in {d['non_resident_in']})")
    for sec in d["consular"]:
        ui.contact_card(sec, "Visa & consular section")
    if d["offices"]:
        st.markdown(f"**{'Offices nearest ' + home if home else 'Consulates and honorary consuls in the UK'}**"
                    + ("" if home else " · choose where you live to sort by distance"))
        shown = d["offices"][:4] if home else d["offices"][:6]
        for o in shown:
            dist = (f"{o['km']} km away" if o["km"] else f"In {home}") if home and o["km"] is not None else None
            ui.contact_card(o, "Consulate" if o["kind"] == "consulate" else "Honorary consulate",
                            covers=o["covers_you"], distance=dist)
        rest = d["offices"][len(shown):]
        if rest:
            with st.expander(f"Show {len(rest)} more office{'s' if len(rest) > 1 else ''}"):
                for o in rest:
                    ui.contact_card(o, "Consulate" if o["kind"] == "consulate" else "Honorary consulate",
                                    covers=o["covers_you"],
                                    distance=f"{o['km']} km away" if home and o["km"] else None)
        st.caption("Honorary consuls are volunteers who represent a country locally. Most can't issue visas, but "
                   "they can often answer questions — phone before you visit.")
    age = lists_age_days()
    if age is not None and age > 92:
        ui.callout("These contact details may be out of date",
                   f"They come from the FCDO lists revised {CONTACTS_META['revised']}. Check the embassy's own website "
                   "before you visit or post documents.", "amber")
    st.markdown(f'<p class="fine">Source: {CONTACTS_META["source"]} (FCDO, revised {CONTACTS_META["revised"]}). '
                'Only public office details are shown.</p>', unsafe_allow_html=True)


tab_check, tab_map, tab_ai, tab_rights, tab_data = st.tabs(
    ["Check a trip", "World map", "Ask the adviser", "Your rights", "Data & sources"])

# ═════════════════════════════════════════════════════════════════════════════
# 1 · CHECK A TRIP
# ═════════════════════════════════════════════════════════════════════════════
with tab_check:
    left, right = st.columns([5, 7], gap="large")

    with left:
        ui.eyebrow("Your trip")
        with st.container(border=True):
            st.selectbox("Where are you going?", DEST_CODES, key="dest", format_func=label,
                         placeholder=f"Search {len(DEST_CODES)} countries…")
            st.selectbox("What's the trip for?", list(PURPOSES), key="purpose", format_func=PURPOSES.get)
            c1, c2 = st.columns(2)
            c1.date_input("Leaving", key="depart", min_value=TODAY, format="DD/MM/YYYY")
            c2.date_input("Coming back", key="ret", min_value=TODAY, format="DD/MM/YYYY")
            st.selectbox("Your travel document", list(DOC_TYPES), key="doc",
                         format_func=lambda k: DOC_TYPES[k]["short"],
                         help="Not sure? The blue document with '1951 Convention' on the cover is a CTD.")
            st.selectbox("Where do you live? (optional)", UK_CITIES, key="city", placeholder="Choose the nearest city",
                         help="We'll show the embassy, plus any consulate or honorary consul near you.")
            with st.expander("More accurate result (optional)"):
                st.selectbox("Country of nationality", ALL_CODES, key="origin", format_func=label,
                             placeholder="Choose a country",
                             help="Refugee travel documents aren't valid for your country of nationality.")
                st.date_input("Document expiry date", key="expiry", min_value=TODAY,
                              format="DD/MM/YYYY")
                st.caption("Nothing you enter is stored. It stays in this browser session only.")

    with right:
        days = (st.session_state.ret - st.session_state.depart).days
        if not st.session_state.dest:
            st.markdown("""<div class="empty"><div class="t">Where are you heading?</div>
<div class="d">Choose a destination to see whether you need a visa with your UK travel document, why,
and exactly what to do next. Or try one of these:</div></div>""", unsafe_allow_html=True)
            st.write("")
            q1, q2, q3 = st.columns(3)
            q1.button("💼 Internship · Romania", on_click=quick_start, args=("RO", "paid_work", 90),
                      use_container_width=True)
            q2.button("🏖️ Holiday · Germany", on_click=quick_start, args=("DE", "tourism", 10),
                      use_container_width=True)
            q3.button("👪 Family · USA", on_click=quick_start, args=("US", "family", 21),
                      use_container_width=True)
        elif days < 1:
            ui.callout("Check your dates", "Your return date needs to be after your departure date.", "amber")
        else:
            trip = Trip(destination=st.session_state.dest, purpose=st.session_state.purpose, days=days,
                        doc_type=st.session_state.doc, origin=st.session_state.origin,
                        depart=st.session_state.depart, doc_expiry=st.session_state.expiry,
                        city=st.session_state.city)
            a = assess(trip)
            ui.verdict_card(a, [ui.plain_chip(f"{days} days · {PURPOSES[trip.purpose]}")])

            if a.actions:
                st.write("")
                ui.eyebrow("What to do next")
                ui.action_list(a.actions)

            near = nearest_office(trip.destination, trip.city) if a.verdict in ("visa", "evisa", "check") else None
            if near:
                st.write("")
                ui.eyebrow(f"Your nearest office")
                ui.contact_card(near, "Consulate" if near["kind"] == "consulate" else "Honorary consulate",
                                highlight=True, covers=near["covers_you"],
                                distance=(f"{near['km']} km from {trip.city}" if near["km"] else f"In {trip.city}"))

            st.write("")
            t_how, t_where, t_list, t_plan, t_letter = st.tabs(
                ["How we decided", "Where to apply", "Checklist", "Timeline", "Embassy letter"])
            with t_where:
                render_directory(trip.destination, trip.city)
            with t_how:
                ui.step_list(a.steps)
            with t_list:
                items = checklist(a)
                key = f"chk_{trip.destination}_{trip.purpose}_{trip.doc_type}"
                done = sum(st.session_state.get(f"{key}_{i}", False) for i in range(len(items)))
                st.progress(done / len(items), text=f"{done} of {len(items)} ready")
                for i, item in enumerate(items):
                    st.checkbox(item, key=f"{key}_{i}")
            with t_plan:
                ui.timeline(journey(a))
            with t_letter:
                st.caption("Send this to the embassy or a consulate, and keep their written reply with your documents.")
                name = st.text_input("Your name", placeholder="As it appears on your travel document")
                letter = embassy_letter(a, name or "[Your name]")
                st.text_area("Email text", letter, height=330, label_visibility="collapsed")
                st.download_button("Download letter", letter, file_name=f"embassy-enquiry-{trip.destination}.txt",
                                   use_container_width=True)

            st.write("")
            st.download_button("⬇  Download trip summary (with contacts)", trip_summary_md(a),
                               file_name=f"secure-path-{a.country['name'].lower().replace(' ', '-')}.md",
                               use_container_width=True, type="primary")
            st.markdown(f'<p class="fine">Guidance only — not legal advice. Rules change; always confirm with the '
                        f'embassy before you travel. Country data reviewed {DATA_REVIEWED}.</p>',
                        unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# 2 · WORLD MAP
# ═════════════════════════════════════════════════════════════════════════════
with tab_map:
    ui.lead("Entry rules for UK refugee travel document holders, country by country. A country is only shown as "
            "visa-free when its own embassy says so — we keep the quote, the link and the date we checked it.")
    rows = [c for c in COUNTRIES.values()]
    counts = {s: sum(1 for c in rows if c["status"] == s) for s in STATUS}
    n_ver = sum(1 for c in rows if c["confidence"] == "verified")
    ui.tiles([(len(rows), "countries covered", None), (n_ver, "embassy-verified", None)] +
             [(counts[s], STATUS[s]["label"], STATUS[s]["color"]) for s in ("visa_free", "evisa", "check", "visa_required")])

    f1, f2, f3 = st.columns([3, 3, 2])
    regions = f1.multiselect("Region", sorted({c["region"] for c in rows}), placeholder="All regions")
    statuses = f2.multiselect("Status", [s for s in STATUS if s != "issuer"], format_func=lambda s: STATUS[s]["label"],
                              placeholder="All statuses")
    query = f3.text_input("Search", placeholder="Country name")
    view = [c for c in rows
            if (not regions or c["region"] in regions)
            and (not statuses or c["status"] in statuses)
            and (not query or query.lower() in c["name"].lower())]

    try:
        import plotly.express as px
        df_map = pd.DataFrame([{"iso3": c["iso3"], "Country": c["name"], "Status": STATUS[c["status"]]["label"],
                                "Confidence": CONFIDENCE[c["confidence"]]["label"]} for c in view])
        fig = px.choropleth(df_map, locations="iso3", color="Status", hover_name="Country",
                            hover_data={"iso3": False, "Status": True, "Confidence": True},
                            color_discrete_map={STATUS[s]["label"]: STATUS[s]["color"] for s in STATUS},
                            category_orders={"Status": [STATUS[s]["label"] for s in
                                                        ("visa_free", "evisa", "check", "visa_required", "issuer")]})
        fig.update_geos(projection_type="natural earth", showframe=False, showcoastlines=False,
                        landcolor="#EEF2F6", showland=True, showcountries=True, countrycolor="#FFFFFF",
                        lataxis_range=[-58, 85], bgcolor="rgba(0,0,0,0)")
        fig.update_traces(marker_line_color="#FFFFFF", marker_line_width=0.5)
        fig.update_layout(height=470, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
                          legend=dict(orientation="h", y=-0.02, x=0.5, xanchor="center", title=None,
                                      font=dict(size=12)),
                          font=dict(family="Inter, sans-serif"), dragmode=False)
        cfg = {"displayModeBar": False}
        if os.getenv("SECURE_PATH_TOPOJSON_URL"):  # offline / locked-down networks: serve map outlines locally
            cfg["topojsonURL"] = os.getenv("SECURE_PATH_TOPOJSON_URL")
        st.plotly_chart(fig, use_container_width=True, config=cfg)
    except ImportError:
        ui.callout("Map unavailable", "Install plotly to see the world map: <code>pip install plotly</code>", "amber")

    df = pd.DataFrame([{
        "Country": f"{c['flag']}  {c['name']}", "Region": c["region"],
        "Status": f"{STATUS[c['status']]['icon']}  {STATUS[c['status']]['label']}",
        "Confidence": CONFIDENCE[c["confidence"]]["label"],
        "Online visa": "Yes" if c["evisa_url"] and c["status"] == "evisa" else "",
        "Schengen": "Yes" if c["schengen"] else "",
    } for c in view])
    st.dataframe(df, hide_index=True, use_container_width=True, height=380)

    ui.eyebrow("Country details")
    pick = st.selectbox("Country details", [c["iso2"] for c in sorted(view, key=lambda c: c["name"])],
                        format_func=label, index=None, placeholder="Choose a country to see details and sources",
                        label_visibility="collapsed")
    if pick:
        c = COUNTRIES[pick]
        st.markdown(f"### {c['flag']} {c['name']}")
        st.markdown(ui.status_chip(c["status"]) + " " + ui.confidence_chip(c["confidence"]), unsafe_allow_html=True)
        st.write(c["summary"])
        if c.get("evidence"):
            ev = c["evidence"]
            st.markdown(f"> “{ev['quote']}”\n>\n> — [{ev['source']['label']}]({ev['source']['url']}), "
                        f"checked {ev['checked']}")
            st.caption(ev["extra"])
            if c.get("by_doc"):
                st.markdown(" · ".join(f"**{DOC_TYPES[k]['short']}:** {STATUS[v]['label']}"
                                       for k, v in c["by_doc"].items()))
        for n in c["notes"]:
            st.markdown(f"- {n}")
        if c["evisa_url"]:
            st.markdown(f"**Official online system:** [{c['evisa_url']}]({c['evisa_url']})")
        with st.expander("Embassy and consulates in the UK"):
            render_directory(pick, st.session_state.city)
        st.markdown("**Sources:** " + " · ".join(f"[{s['label']}]({s['url']})" for s in c["sources"]))

# ═════════════════════════════════════════════════════════════════════════════
# 3 · AI ADVISER
# ═════════════════════════════════════════════════════════════════════════════
def _secret(name):
    try:
        return st.secrets.get(name)
    except Exception:
        return None


env_key = {"anthropic": os.getenv("ANTHROPIC_API_KEY") or _secret("ANTHROPIC_API_KEY"),
           "openai": os.getenv("OPENAI_API_KEY") or _secret("OPENAI_API_KEY")}

with tab_ai:
    h1, h2, h3 = st.columns([6, 2, 2], vertical_alignment="center")
    provider = st.session_state.provider
    key = st.session_state.api_key or env_key.get(provider) or ""
    if not key and not st.session_state.api_key:  # pick whichever provider has a configured key
        for p, k in env_key.items():
            if k:
                provider, key = p, k
                break
    live = bool(key)
    with h1:
        st.markdown("#### Ask the adviser")
        st.markdown(ui.plain_chip("● Live AI · " + ("Claude" if provider == "anthropic" else "OpenAI")) if live else
                    ui.plain_chip("● Rules-engine mode — no API key needed"), unsafe_allow_html=True)
    with h2.popover("AI settings", use_container_width=True):
        st.radio("Provider", ["anthropic", "openai"], key="provider", horizontal=True,
                 format_func=lambda p: "Anthropic (Claude)" if p == "anthropic" else "OpenAI")
        st.text_input("API key", key="api_key", type="password", placeholder="Paste your key")
        st.caption("Get a key at console.anthropic.com or platform.openai.com. The key is used for this "
                   "session only. Live mode sends your messages to the provider; the verdict still comes "
                   "from the Secure Path rules engine.")
    if h3.button("New conversation", use_container_width=True):
        st.session_state.chat, st.session_state.trip_state = [], TripState()
        st.rerun()

    chat_box = st.container()
    with chat_box:
        if not st.session_state.chat:
            st.markdown("""<div class="empty"><div class="t">Describe your trip in your own words</div>
<div class="d">I'll work out the destination, purpose and length, check them against the rules, and show you how
I reached the answer.</div></div>""", unsafe_allow_html=True)
            st.write("")
        for i, m in enumerate(st.session_state.chat):
            with st.chat_message(m["role"], avatar="🛡️" if m["role"] == "assistant" else None):
                st.markdown(m["content"])
                a = m.get("assessment")
                if a:
                    with st.expander("How I worked this out"):
                        ui.step_list(a.steps)

    suggestions = ["Paid internship in Romania for 3 months", "Can I use ESTA for the US?",
                   "Holiday in Spain for 2 weeks", "What is ETS No. 31?"]
    picked = None
    if not st.session_state.chat:
        cols = st.columns(len(suggestions))
        for col, s in zip(cols, suggestions):
            if col.button(s, use_container_width=True):
                picked = s

    prompt = st.chat_input("e.g. I'm visiting my brother in Canada for 3 weeks") or picked
    if prompt:
        history = list(st.session_state.chat)
        st.session_state.chat.append({"role": "user", "content": prompt})
        with st.spinner("Checking the rules…"):
            r = respond(prompt, st.session_state.trip_state, history,
                        {"provider": provider, "key": key} if live else None)
        st.session_state.chat.append({"role": "assistant", "content": r.text, "assessment": r.assessment})
        st.rerun()

    st.markdown('<p class="fine">The adviser explains rules — it is not a lawyer. Always confirm with the '
                'embassy before you travel.</p>', unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# 4 · YOUR RIGHTS
# ═════════════════════════════════════════════════════════════════════════════
with tab_rights:
    ui.lead("The essentials, in plain English.")
    ui.eyebrow("Which document do you have?")
    cols = st.columns(3)
    for col, (k, d) in zip(cols, DOC_TYPES.items()):
        with col:
            ui.card(d["short"], f"<b>For:</b> {d['for']}<br><b>Legal basis:</b> {d['basis']}")
    st.write("")

    ui.eyebrow("Five rules that matter most")
    rules = [
        ("Not valid for your country of nationality",
         "A refugee travel document can't be used to go to the country you're a national of. Going back can put "
         "your refugee status at risk."),
        ("Paid work always needs a permit",
         "Even where visits are visa-free, any paid work or paid internship needs a work visa or permit first."),
        ("Schengen counts days across all countries",
         "Where you're visa-exempt, you get 90 days in any 180, shared across all 29 Schengen countries."),
        ("No ESTA, ETA or visa-on-arrival by default",
         "Most fast-track schemes are tied to nationality. Assume you need a full visa unless confirmed."),
        ("Keep your eVisa up to date",
         "Your UKVI account must show your current travel document, or airlines may not let you board home."),
    ]
    r1, r2 = st.columns(2)
    for i, (t, d) in enumerate(rules):
        with (r1 if i % 2 == 0 else r2):
            ui.card(f"{i + 1}. {t}", d)
            st.write("")

    ui.eyebrow("Questions people ask")
    for title, k in [("What is ETS No. 31, and does it still help me?", "ets31"),
                     ("What is a Convention Travel Document?", "ctd"),
                     ("Can I visit my home country?", "origin"),
                     ("How does the Schengen 90/180 rule work?", "schengen"),
                     ("Can I use ESTA to visit the USA?", "esta"),
                     ("What do I need to do with my UK eVisa?", "evisa_uk"),
                     ("How long must my document be valid?", "validity")]:
        with st.expander(title):
            st.markdown(FAQ[k])

    ui.eyebrow("Get help")
    g1, g2, g3 = st.columns(3)
    with g1:
        ui.card("Apply or renew", 'Travel documents are issued by the Home Office. '
                '<a href="https://www.gov.uk/apply-home-office-travel-documents" target="_blank">GOV.UK guide ↗</a>')
    with g2:
        ui.card("Free advice", '<a href="https://www.refugeecouncil.org.uk/" target="_blank">Refugee Council ↗</a> · '
                '<a href="https://www.migranthelpuk.org/" target="_blank">Migrant Help ↗</a> · '
                '<a href="https://www.citizensadvice.org.uk/" target="_blank">Citizens Advice ↗</a>')
    with g3:
        ui.card("Before you go", '<a href="https://www.gov.uk/foreign-travel-advice" target="_blank">'
                'FCDO travel advice ↗</a> for safety, entry rules and local laws.')

# ═════════════════════════════════════════════════════════════════════════════
# 5 · DATA & SOURCES
# ═════════════════════════════════════════════════════════════════════════════
with tab_data:
    ui.lead("How Secure Path decides, and how far you can rely on it.")
    ui.callout("Key legal finding: UK documents no longer benefit from ETS No. 31",
               "The UK suspended the 1959 European Agreement on the Abolition of Visas for Refugees in 2003. "
               "Article 7(2) says a state that suspends it “may not claim the application of this Agreement by any "
               "other Party”. For Schengen countries, visa-free travel for UK-resident refugees now depends on each "
               "state's choice under EU Regulation 2018/1806, Art. 6(2). France (1986) and Ireland (2022) have also "
               "suspended the agreement.", "blue")

    ui.eyebrow("Confidence levels")
    cc = st.columns(len(CONFIDENCE))
    for col, (k, v) in zip(cc, CONFIDENCE.items()):
        n = sum(1 for c in COUNTRIES.values() if c["confidence"] == k)
        with col:
            ui.card(f"{v['label']} · {n} countries", v["help"])
    st.write("")

    ui.eyebrow("How a decision is made")
    st.markdown("""
1. **Document check:** which UK travel document you hold, and whether the destination is your country of nationality.
2. **Destination rule:** the country's rule for that document, with its confidence level and sources.
3. **Purpose:** paid work, study, volunteering and transit each have their own rules.
4. **Length of stay:** short-stay limits, including the Schengen 90/180 rule.
5. **Document validity:** how long your document must be valid after you leave.
6. **Timing and safety:** when to apply, plus FCDO travel warnings.

The Trip Checker and the AI adviser use **the same rules engine**, so they always agree. In live mode the AI
explains the engine's verdict but can't change it.
""")
    st.write("")
    ui.eyebrow("Design principle: safe by default")
    st.markdown("A country is shown as **visa-free only when its own embassy or government says so** for UK-issued "
                "travel documents. Treaty lists, secondary guides and online summaries can't make a country "
                "visa-free here: in October 2026 they disagreed with the Belgian and Spanish embassies, which both "
                "require a Schengen visa. Wrongly telling someone they can travel visa-free costs far more (refused "
                "boarding or entry) than telling them to check.")
    st.write("")
    ui.eyebrow("How the data stays accurate")
    st.markdown("""
1. **Evidence, not claims:** every embassy-verified rule stores a verbatim quote, the official URL and the date checked.
2. **Rules per document:** blue, red and black documents are recorded separately, because embassies treat them differently.
3. **Expiry:** evidence older than 180 days automatically stops counting as visa-free and falls back to "confirm".
4. **Change monitoring:** a script (`tools/monitor_sources.py`) re-fetches each official page and flags any change for human review.
5. **Written confirmation:** for unverified countries, the app drafts a letter so travellers get the embassy's answer in writing.
6. **Reports from users:** anyone can report outdated information (below); in a live service, reports go to a review queue.
""")
    st.write("")
    ui.eyebrow("Sources")
    for s in SOURCES.values():
        tag = "Official" if s["kind"] == "official" else "Secondary"
        st.markdown(f"- [{s['label']}]({s['url']}) · *{tag}*")
    st.write("")
    ui.eyebrow("Spotted something out of date?")
    with st.form("report", clear_on_submit=True, border=True):
        fc1, fc2 = st.columns([1, 2])
        fc1.selectbox("Country", ALL_CODES, format_func=label, index=None, placeholder="Choose")
        fc2.text_input("What's changed?", placeholder="e.g. The embassy confirmed visa-free entry in September 2026")
        if st.form_submit_button("Send report"):
            st.success("Thank you. In the live service, reports go to the data team for review within 5 working days.")
    st.markdown(f'<p class="fine">Data reviewed {DATA_REVIEWED}. Secure Path is a final-year GovTech prototype '
                f'(Manchester Metropolitan University) and does not give legal advice.</p>', unsafe_allow_html=True)
