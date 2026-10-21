"""
Secure Path — Main Streamlit Application
GovTech platform for Convention Travel Document holders.

v2.0 — Agentic AI Travel Adviser
Adds an AI-powered chat tab that reasons through nuanced CTD eligibility questions,
including the critical ETS No. 31 Article 1(2) paid/unpaid work distinction.

Research prototype — does not constitute legal advice.
"""

import streamlit as st
import sys
import os
import re

sys.path.insert(0, os.path.dirname(__file__))
from engine import check_eligibility, get_document_checklist, get_journey_steps
from data import ALL_COUNTRIES, PURPOSES, CTD_INFO, AI_LEGAL_CONTEXT, ETS_31_COUNTRIES, BILATERAL_COUNTRIES


# ══════════════════════════════════════════════════════════════════════════════
# DEMO AI — must be defined before the tab that calls it
# ══════════════════════════════════════════════════════════════════════════════
def _demo_ai_response(user_input: str, history: list) -> str:
    """
    Rule-based agentic reasoning engine for demo mode.
    Parses user intent and applies CTD legal rules step by step.
    """
    text = user_input.lower()
    all_history = " ".join([m["content"].lower() for m in history])

    # ── Detect country ────────────────────────────────────────────────────
    detected_country = None
    for country in list(ETS_31_COUNTRIES.keys()) + list(BILATERAL_COUNTRIES.keys()):
        if country.lower() in text or country.lower() in all_history:
            detected_country = country
            break

    # ── Detect purpose signals ───────────────────────────────────────────
    is_paid_work = any(kw in text for kw in [
        "paid internship", "paid work", "job", "salary", "employment", "work permit",
        "internship", "working", "earning", "stipend", "remuneration"
    ])
    is_unpaid = any(kw in text for kw in [
        "volunteer", "voluntary", "unpaid", "charity", "ngo", "placement"
    ])
    is_study = any(kw in text for kw in ["study", "university", "masters", "phd", "degree", "student"])
    is_holiday = any(kw in text for kw in ["holiday", "tourism", "tourist", "visit", "vacation"])

    # ── Detect duration ──────────────────────────────────────────────────
    duration_match = re.search(r'(\d+)\s*(day|week|month)', text)
    duration_days = None
    if duration_match:
        num = int(duration_match.group(1))
        unit = duration_match.group(2)
        if unit == "week":
            duration_days = num * 7
        elif unit == "month":
            duration_days = num * 30
        else:
            duration_days = num

    # ── Greetings / small talk — only if no country or purpose detected ──
    is_greeting = any(kw in text for kw in ["hello", "hi", "hey", "what can you"])
    is_just_help = "help" in text and not detected_country and not (is_paid_work or is_unpaid or is_study or is_holiday)
    if is_greeting or is_just_help:
        return (
            "Hello! I'm here to help you navigate travel with your UK Convention Travel Document (CTD).\n\n"
            "The most important thing I do differently from a simple lookup is reason through the **specific details** of your trip — "
            "especially the **purpose** of your travel, which dramatically changes what visa rules apply.\n\n"
            "For example, did you know that going to Romania for a **paid internship** requires a work visa, "
            "even though Romania is an ETS No. 31 signatory country? A standard lookup would tell you 'no visa needed' — "
            "which would be dangerously wrong.\n\n"
            "Tell me: where are you travelling, what for, and how long are you planning to stay?"
        )

    # ── Paid internship in ETS 31 country ───────────────────────────────
    if detected_country and detected_country in ETS_31_COUNTRIES and is_paid_work:
        return f"""**🔍 Analysing your situation step by step...**

**Your trip:** Paid work/internship → **{detected_country}** ({f'{duration_days} days' if duration_days else 'duration TBC'})

---

**Step 1: Is {detected_country} an ETS No. 31 country?**
✅ Yes — {detected_country} ratified the 1959 Strasbourg Agreement.

**Step 2: Does ETS No. 31 cover paid work?**
🔴 **No. This is the critical rule.**

Under **ETS No. 31 Article 1(2)**, the visa-free entitlement applies only to **non-gainful purposes**. A **paid internship** is classified as **gainful employment**, so the visa-free exemption **does not apply**.

**Step 3: What do you actually need?**
🔴 **You need a work visa / work permit** issued by {detected_country}.

---

**What to do next:**
1. Contact the {detected_country} embassy in London for work visa requirements
2. Ask your employer to begin the sponsorship/work permit process early (allow 8–12 weeks)
3. Do not book flights until the work visa is confirmed

⚠️ *Guidance based on ETS No. 31 Article 1(2). Verify with the {detected_country} embassy before travelling.*"""

    # ── Unpaid voluntary work in ETS 31 country ─────────────────────────
    if detected_country and detected_country in ETS_31_COUNTRIES and is_unpaid:
        over = duration_days and duration_days > 90
        return f"""**🔍 Analysing your situation...**

**Your trip:** Unpaid voluntary work → **{detected_country}** ({f'{duration_days} days' if duration_days else 'duration TBC'})

---

✅ **Good news — your visa-free rights are preserved.**

Under **ETS No. 31 Article 1(2)**, unpaid voluntary work is **NOT classified as gainful employment**. Your CTD entitles you to visa-free entry to {detected_country} for up to 90 days.

{"⚠️ However, your stay of " + str(duration_days) + " days exceeds the 90-day limit — you would need a long-stay visa." if over else f"✅ Your stay of {duration_days} days is within the 90-day limit." if duration_days else ""}

**Carry with you:** CTD (valid 6+ months beyond return), letter confirming unpaid placement, proof of funds, accommodation, and travel insurance.

⚠️ *Guidance only. Verify with the {detected_country} embassy before travelling.*"""

    # ── General ETS 31 visit ─────────────────────────────────────────────
    if detected_country and detected_country in ETS_31_COUNTRIES:
        over = duration_days and duration_days > 90
        return f"""**🔍 Analysing your trip to {detected_country}...**

{"⚠️ **Duration Alert:** Your planned stay of " + str(duration_days) + " days exceeds the 90-day visa-free limit. You would need a long-stay visa even though " + detected_country + " is an ETS No. 31 signatory." if over else "✅ **No visa required** for this trip under normal circumstances."}

**Why:** {detected_country} has ratified the **1959 Strasbourg Agreement (ETS No. 31)**, which grants CTD holders visa-free entry for non-gainful purposes for up to 90 days.

**One important question:** If any part of the trip involves **paid work or a paid internship**, the answer changes completely — paid work requires a work visa even in ETS No. 31 countries under Article 1(2).

⚠️ *Some embassies incorrectly require visas for non-gainful ETS 31 travel. If this happens, cite ETS No. 31 directly.*"""

    # ── Bilateral countries ───────────────────────────────────────────────
    if detected_country and detected_country in BILATERAL_COUNTRIES:
        info = BILATERAL_COUNTRIES[detected_country]
        if info["visa_required"]:
            evisa_note = f"\n\n🌐 **eVisa available:** {info['evisa_info']}" if info.get("evisa") else ""
            return f"""**🔍 Analysing your trip to {detected_country}...**

🔴 **Visa required** — {detected_country} is not an ETS No. 31 signatory and requires a visa from CTD holders.

**Legal note:** {info['notes']}{evisa_note}

Apply well in advance (at least 8 weeks). Ensure your CTD is valid for 6+ months beyond your return date.

⚠️ *Guidance only. Verify with the {detected_country} embassy before booking.*"""
        else:
            return f"""**🔍 Analysing your trip to {detected_country}...**

✅ **No visa required** under a bilateral arrangement between the UK and {detected_country}.

**Note:** {info['notes']}

⚠️ *Guidance only. Always confirm requirements with official sources before travelling.*"""

    # ── Study ─────────────────────────────────────────────────────────────
    if is_study and detected_country:
        return f"""**🔍 Analysing your study trip to {detected_country}...**

📚 **Study typically requires a student visa**, even in ETS No. 31 countries.

Contact {detected_country}'s embassy in London or the international student office at your institution for exact requirements. You'll typically need: student visa, enrolment letter, proof of funds, accommodation, and travel insurance.

⚠️ *Student visa rules vary significantly by country and course type.*"""

    # ── Need more info ────────────────────────────────────────────────────
    missing = []
    if not detected_country:
        missing.append("**destination country**")
    if not (is_paid_work or is_unpaid or is_study or is_holiday):
        missing.append("**purpose of your trip** (paid work, volunteer, tourism, study?)")
    if not duration_days:
        missing.append("**how long** you plan to stay")

    if missing:
        return (
            f"To give you accurate guidance, I need a couple more details:\n\n"
            + "\n".join(f"- {m}" for m in missing)
            + "\n\nFor example: *'I'm going to Romania for a paid 3-month internship'* or "
            "*'I want to visit France for 2 weeks as a tourist'*.\n\n"
            "The **purpose** of your trip is especially important — whether work is paid or unpaid "
            "can completely change the visa requirements under ETS No. 31 Article 1(2)."
        )

    return (
        "Could you clarify a few things?\n\n"
        "- Is this trip for **paid work**, **unpaid volunteering**, **tourism**, or **study**?\n"
        "- Which **country** are you travelling to?\n"
        "- How long is the planned stay?\n\n"
        "These details are crucial — especially whether any work is paid, as this affects your rights under ETS No. 31."
    )

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Secure Path",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CUSTOM CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
  }

  .main { background: #F8FAFC; }

  /* Hero */
  .hero {
    background: linear-gradient(135deg, #0A1628 0%, #1E3A8A 60%, #2563EB 100%);
    padding: 3rem 2.5rem 2.5rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    color: white;
  }
  .hero h1 { font-size: 2.8rem; font-weight: 700; margin: 0; letter-spacing: -1px; }
  .hero .subtitle { font-size: 1.1rem; opacity: 0.85; margin-top: 0.5rem; font-weight: 300; }
  .hero .badge {
    display: inline-block;
    background: rgba(245,158,11,0.2);
    border: 1px solid #F59E0B;
    color: #FCD34D;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-bottom: 1rem;
  }
  .disclaimer {
    background: rgba(255,255,255,0.1);
    border-left: 3px solid #F59E0B;
    padding: 0.6rem 1rem;
    border-radius: 0 8px 8px 0;
    font-size: 0.8rem;
    opacity: 0.9;
    margin-top: 1.5rem;
  }

  /* Cards */
  .result-card {
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 1rem;
  }
  .visa-free { background: #ECFDF5; border-left: 5px solid #059669; }
  .visa-required { background: #FEF2F2; border-left: 5px solid #DC2626; }
  .check-required { background: #FFFBEB; border-left: 5px solid #D97706; }

  .verdict-title { font-size: 1.4rem; font-weight: 700; margin-bottom: 0.4rem; }
  .verdict-free .verdict-title { color: #065F46; }
  .verdict-required .verdict-title { color: #991B1B; }
  .verdict-check .verdict-title { color: #92400E; }

  /* Warning / info boxes */
  .warning-box {
    background: #FFFBEB;
    border: 1px solid #FCD34D;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    font-size: 0.9rem;
    color: #78350F;
  }
  .info-box {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    font-size: 0.9rem;
    color: #1E3A8A;
  }
  .note-box {
    background: #F5F3FF;
    border: 1px solid #C4B5FD;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    font-size: 0.9rem;
    color: #4C1D95;
  }
  .critical-box {
    background: #FEF2F2;
    border: 2px solid #DC2626;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
    font-size: 0.9rem;
    color: #7F1D1D;
  }

  /* Checklist */
  .checklist-item {
    display: flex;
    align-items: flex-start;
    padding: 0.7rem 0.9rem;
    margin: 0.3rem 0;
    border-radius: 8px;
    font-size: 0.92rem;
    line-height: 1.5;
  }
  .checklist-required { background: #F0FDF4; border: 1px solid #BBF7D0; color: #14532D; }
  .checklist-optional { background: #F8FAFC; border: 1px solid #E2E8F0; color: #475569; }
  .check-icon { margin-right: 0.7rem; font-size: 1rem; flex-shrink: 0; margin-top: 1px; }

  /* Steps */
  .step-card {
    display: flex;
    align-items: flex-start;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
    border-radius: 10px;
    border: 1px solid #E2E8F0;
    background: white;
  }
  .step-number {
    width: 36px; height: 36px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 0.9rem;
    flex-shrink: 0; margin-right: 1rem; margin-top: 2px;
  }
  .step-complete .step-number { background: #059669; color: white; }
  .step-action .step-number { background: #2563EB; color: white; }
  .step-info .step-number { background: #64748B; color: white; }
  .step-title { font-weight: 600; font-size: 0.95rem; color: #1E293B; margin-bottom: 0.2rem; }
  .step-timeframe { font-size: 0.78rem; color: #94A3B8; margin-bottom: 0.3rem; font-weight: 500; }
  .step-detail { font-size: 0.88rem; color: #475569; line-height: 1.5; }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    border-bottom: 2px solid #E2E8F0;
  }
  .stTabs [data-baseweb="tab"] {
    font-weight: 500;
    font-size: 0.9rem;
    padding: 0.6rem 1.2rem;
    border-radius: 8px 8px 0 0;
  }

  /* Section headers */
  .section-header {
    font-size: 1.1rem;
    font-weight: 700;
    color: #0A1628;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #1E3A8A;
    margin-bottom: 1rem;
    margin-top: 1.5rem;
  }

  /* CTD info */
  .ctd-fact {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.4rem 0;
    font-size: 0.88rem;
    color: #334155;
  }
  .ctd-fact strong { color: #0A1628; }

  /* AI chat panel */
  .ai-intro {
    background: linear-gradient(135deg, #0A1628 0%, #1E3A8A 100%);
    border-radius: 12px;
    padding: 1.5rem 2rem;
    color: white;
    margin-bottom: 1.5rem;
  }
  .ai-intro h3 { margin: 0 0 0.5rem 0; font-size: 1.2rem; }
  .ai-intro p { margin: 0; font-size: 0.9rem; opacity: 0.85; }
  .ai-example-chip {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.3);
    color: white;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    margin: 0.3rem 0.2rem 0 0;
    cursor: pointer;
  }
  .demo-banner {
    background: #FFFBEB;
    border: 1px solid #FCD34D;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 1rem;
    font-size: 0.88rem;
    color: #78350F;
  }
</style>
""", unsafe_allow_html=True)


# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="badge">🛡️ RESEARCH PROTOTYPE · MMU 5Z6Z1002</div>
  <h1>Secure Path</h1>
  <div class="subtitle">Visa eligibility & document guidance for UK Convention Travel Document holders</div>
  <div class="disclaimer">
    ⚠️ <strong>Research Prototype.</strong> This tool is built for academic demonstration purposes.
    It does not constitute legal advice. Always verify requirements with the official embassy before travelling.
  </div>
</div>
""", unsafe_allow_html=True)


# ─── MAIN TABS ───────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍  Eligibility Checker",
    "📋  Document Checklist",
    "ℹ️  About My CTD",
    "🤖  AI Travel Adviser"
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ELIGIBILITY CHECKER
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">Check Your Travel Eligibility</div>', unsafe_allow_html=True)
    st.markdown("Enter your travel details below to find out if you need a visa and what you'll need to prepare.")

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        destination = st.selectbox(
            "🌍 Where are you travelling to?",
            options=["Select a country…"] + ALL_COUNTRIES,
            help="Select your destination country"
        )

    with col2:
        purpose = st.selectbox(
            "✈️ What is the purpose of your trip?",
            options=PURPOSES,
            help="Choose the main reason for your travel"
        )

    with col3:
        duration = st.number_input(
            "📅 How many days?",
            min_value=1,
            max_value=365,
            value=14,
            help="Total number of days you plan to stay"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    check_btn = st.button("🔍  Check My Eligibility", type="primary", use_container_width=True)

    if check_btn and destination != "Select a country…":
        with st.spinner("Checking eligibility…"):
            result = check_eligibility(destination, purpose, duration)

        st.markdown("---")

        # ── Verdict card ──
        verdict_class = {"visa_free": "visa-free", "visa_required": "visa-required", "check_required": "check-required"}[result["verdict"]]
        color_class = {"visa_free": "verdict-free", "visa_required": "verdict-required", "check_required": "verdict-check"}[result["verdict"]]

        st.markdown(f"""
        <div class="result-card {verdict_class} {color_class}">
          <div class="verdict-title">{result['verdict_label']}</div>
          <div style="font-size:0.95rem; color:#334155; margin-top:0.3rem;">{result['key_message']}</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Article 1(2) critical alert ──
        if result.get("article_1_2_applies"):
            st.markdown(f"""
            <div class="critical-box">
              📌 <strong>ETS No. 31 Article 1(2) — Critical Rule:</strong><br>
              The 1959 Strasbourg Agreement grants visa-free travel for <em>non-gainful purposes only</em>.
              A paid internship or employment is "gainful employment" under Article 1(2), which means the
              visa-free exemption is <strong>not available</strong> — even in ETS No. 31 signatory countries.
              This applies to <strong>{destination}</strong>.
            </div>
            """, unsafe_allow_html=True)

        # ── Legal basis ──
        if result["legal_basis"]:
            st.markdown(f'<div class="info-box">📜 <strong>Legal basis:</strong> {result["legal_basis"]}</div>', unsafe_allow_html=True)

        # ── eVisa warning ──
        if result["evisa_required"] and result["evisa_info"]:
            st.markdown(f'<div class="warning-box">🌐 <strong>eVisa required:</strong> {result["evisa_info"]}</div>', unsafe_allow_html=True)

        # ── Purpose-specific note ──
        if result["important_note"]:
            st.markdown(f'<div class="note-box">📌 <strong>Important for your trip purpose:</strong> {result["important_note"]}</div>', unsafe_allow_html=True)

        # ── Warnings ──
        for w in result["warnings"]:
            st.markdown(f'<div class="warning-box">{w}</div>', unsafe_allow_html=True)

        # ── Walking Border Journey Steps ──
        st.markdown('<div class="section-header">Your Step-by-Step Journey Plan</div>', unsafe_allow_html=True)
        steps = get_journey_steps(destination, purpose, result["visa_required"] or False, result["evisa_required"])

        for step in steps:
            status_class = f"step-{step['status']}"
            st.markdown(f"""
            <div class="step-card {status_class}">
              <div class="step-number">{step['step']}</div>
              <div style="flex:1">
                <div class="step-title">{step['title']}</div>
                <div class="step-timeframe">⏱ {step['timeframe']}</div>
                <div class="step-detail">{step['detail']}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Suggest AI adviser for complex cases ──
        if result["article_1_2_applies"] or result["verdict"] == "check_required":
            st.markdown("""
            <div class="info-box" style="margin-top:1rem">
              💬 <strong>Need more personalised advice?</strong>
              Try the <strong>🤖 AI Travel Adviser</strong> tab — it can reason through complex situations,
              ask you clarifying questions, and explain the law in plain language.
            </div>
            """, unsafe_allow_html=True)

    elif check_btn and destination == "Select a country…":
        st.warning("Please select a destination country first.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DOCUMENT CHECKLIST
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Get Your Document Checklist</div>', unsafe_allow_html=True)
    st.markdown("Tell us where you're going and why — we'll generate a personalised checklist of everything you need.")

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        dest2 = st.selectbox("🌍 Destination", options=["Select a country…"] + ALL_COUNTRIES, key="dest2")
    with c2:
        purpose2 = st.selectbox("✈️ Purpose of travel", options=PURPOSES, key="purpose2")
    with c3:
        visa_needed = st.selectbox("🔑 Visa required?", options=["Not sure", "Yes", "No"], key="visa2")

    gen_btn = st.button("📋  Generate My Checklist", type="primary", use_container_width=True)

    if gen_btn and dest2 != "Select a country…":
        if visa_needed == "Not sure":
            quick_check = check_eligibility(dest2, purpose2, 14)
            visa_bool = quick_check["visa_required"] or False
        else:
            visa_bool = visa_needed == "Yes"

        checklist = get_document_checklist(dest2, purpose2, visa_bool)

        st.markdown("---")
        st.markdown(f"### Documents for: **{dest2}** · {purpose2}")

        st.markdown('<div class="section-header">✅ Always Required</div>', unsafe_allow_html=True)
        for item in checklist["always_required"]:
            st.markdown(f"""
            <div class="checklist-item checklist-required">
              <span class="check-icon">✅</span>
              <span>{item}</span>
            </div>
            """, unsafe_allow_html=True)

        if checklist["sometimes_required"]:
            st.markdown('<div class="section-header">⚠️ May Also Be Required</div>', unsafe_allow_html=True)
            st.caption("Check with the embassy or consulate to confirm which of these apply to your specific situation.")
            for item in checklist["sometimes_required"]:
                st.markdown(f"""
                <div class="checklist-item checklist-optional">
                  <span class="check-icon">📎</span>
                  <span>{item}</span>
                </div>
                """, unsafe_allow_html=True)

        if checklist["important_note"]:
            st.markdown(f'<div class="note-box" style="margin-top:1rem">📌 <strong>Important note for your trip type:</strong><br>{checklist["important_note"]}</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        checklist_text = f"SECURE PATH — Document Checklist\n{'='*50}\nDestination: {dest2}\nPurpose: {purpose2}\n\nALWAYS REQUIRED:\n"
        for i, item in enumerate(checklist["always_required"], 1):
            checklist_text += f"  {i}. {item}\n"
        if checklist["sometimes_required"]:
            checklist_text += "\nMAY ALSO BE REQUIRED:\n"
            for i, item in enumerate(checklist["sometimes_required"], 1):
                checklist_text += f"  {i}. {item}\n"
        checklist_text += "\n⚠️ Research prototype. Verify requirements with the official embassy before travelling."

        st.download_button(
            label="⬇️  Download Checklist as .txt",
            data=checklist_text,
            file_name=f"SecurePath_Checklist_{dest2.replace(' ', '_')}.txt",
            mime="text/plain",
        )

    elif gen_btn:
        st.warning("Please select a destination country first.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ABOUT MY CTD
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Understanding Your Convention Travel Document</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**What is it?**")
        st.markdown(f"""
        <div class="ctd-fact">
          The <strong>Convention Travel Document (CTD)</strong> — also called a Refugee Travel Document or Blue Travel Document —
          is issued by the UK Home Office to people who have been granted refugee status or humanitarian protection.
          It is not a passport, but it is a legally recognised travel document under the
          <strong>1951 UN Refugee Convention, Article 28</strong>.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Key Facts**")
        facts = [
            ("Valid for", "10 years (adults) / 5 years (under 16)"),
            ("Issued by", "UK Home Office"),
            ("Legal basis", "1951 UN Refugee Convention, Article 28"),
            ("Looks like", "A dark blue booklet, similar in size to a passport"),
        ]
        for label, value in facts:
            st.markdown(f'<div class="ctd-fact"><strong>{label}:</strong> {value}</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown("**Your Rights**")
        for right in CTD_INFO["key_rights"]:
            st.markdown(f'<div class="checklist-item checklist-required"><span class="check-icon">✅</span><span>{right}</span></div>', unsafe_allow_html=True)

        st.markdown("**Important Limitations**")
        for limit in CTD_INFO["key_limitations"]:
            st.markdown(f'<div class="checklist-item checklist-optional"><span class="check-icon">⚠️</span><span>{limit}</span></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-header">The 1959 Strasbourg Agreement (ETS No. 31)</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
      <strong>What it means for you:</strong> The Strasbourg Agreement is an international treaty that grants CTD holders the right to travel
      visa-free to signatory countries for short stays (typically up to 90 days) for <em>non-gainful purposes</em>.<br><br>
      <strong>The key problem:</strong> Many embassies and border officers are unaware of this treaty, and sometimes give incorrect advice —
      telling CTD holders they need a visa when they legally do not. This is one of the core problems Secure Path is designed to solve.<br><br>
      <strong>⚠️ Critical nuance — Article 1(2):</strong> The visa-free rights do NOT apply to gainful employment (paid work).
      If you're doing a paid internship in an ETS No. 31 country, you still need a work visa.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**What to say if an embassy gives you wrong information (for non-gainful visits):**")
    st.code(
        'I am a holder of a UK Convention Travel Document issued under the 1951 Refugee Convention. '
        'Under the 1959 Council of Europe Agreement on the Abolition of Visas for Refugees '
        '(ETS No. 31), to which [COUNTRY] is a signatory, I am entitled to visa-free entry '
        'for stays of up to 90 days for non-gainful purposes. I respectfully request that this be reviewed.',
        language=None
    )

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:#94A3B8; font-size:0.8rem; padding: 1rem 0;">
      Secure Path · Research Prototype · MMU Business Technology Project 5Z6Z1002 · 2026/27<br>
      This tool does not constitute legal advice. Always verify with official sources before travelling.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — AI TRAVEL ADVISER (AGENTIC AI)
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    # ── AI intro panel ──────────────────────────────────────────────────────
    st.markdown("""
    <div class="ai-intro">
      <h3>🤖 AI Travel Adviser — Powered by Agentic AI</h3>
      <p>
        Unlike a simple lookup, this AI adviser reasons through your <em>specific situation</em>.
        Tell it your destination, purpose, and duration — and it will ask clarifying questions,
        apply the relevant law (including ETS No. 31 Article 1(2) on paid vs unpaid work),
        and give you a personalised answer with legal citations.
      </p>
      <br>
      <p style="font-size:0.8rem; opacity:0.7">Try asking about:</p>
      <span class="ai-example-chip">Paid internship in Romania</span>
      <span class="ai-example-chip">Volunteering in France for 3 months</span>
      <span class="ai-example-chip">Holiday to Turkey for 2 weeks</span>
      <span class="ai-example-chip">Study in Germany for 1 year</span>
    </div>
    """, unsafe_allow_html=True)

    # ── OpenAI API key setup ──────────────────────────────────────────────────
    # Check for API key in environment or session state
    api_key = os.environ.get("OPENAI_API_KEY", "")

    if not api_key:
        with st.expander("🔑 Connect OpenAI API (optional — demo mode works without this)", expanded=False):
            st.markdown("""
            To use the live AI adviser, enter your OpenAI API key below.
            Your key is never stored — it only lives in this session.

            Don't have one? The **demo mode** below shows exactly how the AI reasons
            through your situation using the same logic.
            """)
            entered_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
            if entered_key:
                st.session_state["openai_key"] = entered_key
                api_key = entered_key
                st.success("✅ API key set for this session.")

    # Use session state key if available
    if "openai_key" in st.session_state:
        api_key = st.session_state["openai_key"]

    use_live_ai = bool(api_key)

    if not use_live_ai:
        st.markdown("""
        <div class="demo-banner">
          🎓 <strong>Demo Mode</strong> — Running without an OpenAI API key.
          The AI adviser below uses rule-based agentic reasoning to demonstrate how personalised
          guidance works. This shows the exact logic that would power the live AI.
          To enable the full conversational AI, add your OpenAI API key above.
        </div>
        """, unsafe_allow_html=True)

    # ── Chat history ────────────────────────────────────────────────────────
    if "ai_messages" not in st.session_state:
        st.session_state["ai_messages"] = [
            {
                "role": "assistant",
                "content": (
                    "Hello! I'm your Secure Path AI Travel Adviser. I specialise in travel guidance "
                    "for UK Convention Travel Document (CTD) holders.\n\n"
                    "I can help you understand:\n"
                    "- Whether you need a visa for your destination\n"
                    "- The impact of your trip **purpose** (paid work, voluntary, tourism, study)\n"
                    "- The critical difference between paid and unpaid work under ETS No. 31\n"
                    "- What documents you'll need and how to handle embassy misinformation\n\n"
                    "Tell me about your travel plans — where are you going, what for, and how long?"
                )
            }
        ]

    # ── Display chat history ────────────────────────────────────────────────
    for msg in st.session_state["ai_messages"]:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

    # ── Chat input ──────────────────────────────────────────────────────────
    user_input = st.chat_input("Ask me about your travel situation…")

    if user_input:
        # Add user message to history
        st.session_state["ai_messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        # ── Generate AI response ──────────────────────────────────────────
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking through your situation…"):

                if use_live_ai:
                    # ── LIVE AI (OpenAI) ──────────────────────────────────
                    try:
                        from openai import OpenAI
                        client = OpenAI(api_key=api_key)

                        system_prompt = f"""You are the Secure Path AI Travel Adviser — a specialised AI assistant for UK Convention Travel Document (CTD) holders.

Your purpose is to give personalised, legally accurate travel guidance based on the user's specific situation. You reason through their situation step by step, asking clarifying questions when needed.

AUTHORITATIVE LEGAL KNOWLEDGE BASE:
{AI_LEGAL_CONTEXT}

BEHAVIOUR GUIDELINES:
1. Always ask about the PURPOSE of travel (paid/unpaid, tourism, study) and DURATION before giving a verdict — these are critical to the answer.
2. For ETS No. 31 countries: the visa-free entitlement ONLY applies to non-gainful purposes. ALWAYS check if the purpose involves payment.
3. The Romania paid internship example is the classic case: Romania IS an ETS 31 country, but a PAID internship = gainful employment = work visa required under Article 1(2). Many people get this wrong.
4. Be conversational but precise. Use plain English and explain the law clearly.
5. Always cite the specific legal basis (e.g. "ETS No. 31 Article 1(2)").
6. Flag common mistakes proactively (ESTA doesn't apply, CTD needs 6+ months validity, etc).
7. End serious visa-required answers with: "⚠️ This is guidance only. Please verify with the relevant embassy before booking."
8. Never make up countries or rules not in your knowledge base — say "I'd need to check that" if unsure.
9. Be empathetic — CTD holders often face frustrating bureaucracy and embassy misinformation. Acknowledge this.

FORMAT: Use clear markdown. Short paragraphs. Bold key conclusions. Use ✅ for safe / 🔴 for visa required / ⚠️ for warnings."""

                        messages_for_api = [{"role": "system", "content": system_prompt}]
                        for msg in st.session_state["ai_messages"]:
                            messages_for_api.append({"role": msg["role"], "content": msg["content"]})

                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=messages_for_api,
                            max_tokens=800,
                            temperature=0.3,  # Low temp for factual accuracy
                        )
                        ai_response = response.choices[0].message.content

                    except ImportError:
                        ai_response = "⚠️ OpenAI library not installed. Run `pip install openai` and restart the app."
                    except Exception as e:
                        ai_response = f"⚠️ AI error: {str(e)}\n\nFalling back to rule-based reasoning — please try the Eligibility Checker tab."

                else:
                    # ── DEMO MODE — Rule-based agentic reasoning ──────────
                    ai_response = _demo_ai_response(user_input, st.session_state["ai_messages"])

                st.markdown(ai_response)

        st.session_state["ai_messages"].append({"role": "assistant", "content": ai_response})

    # ── Clear chat button ──────────────────────────────────────────────────
    col_clear, col_spacer = st.columns([1, 4])
    with col_clear:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state["ai_messages"] = [
                {
                    "role": "assistant",
                    "content": (
                        "Chat cleared. I'm ready to help with your travel questions. "
                        "Tell me about your destination, purpose, and how long you're planning to stay."
                    )
                }
            ]
            st.rerun()

