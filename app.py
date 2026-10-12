"""
Secure Path — Main Streamlit Application
GovTech platform for Convention Travel Document holders.
Research prototype — does not constitute legal advice.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from engine import check_eligibility, get_document_checklist, get_journey_steps
from data import ALL_COUNTRIES, PURPOSES, CTD_INFO

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

  /* Warning box */
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

  /* CTD info box */
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
tab1, tab2, tab3 = st.tabs(["🔍  Eligibility Checker", "📋  Document Checklist", "ℹ️  About My CTD"])


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
        # Auto-determine if not specified
        if visa_needed == "Not sure":
            quick_check = check_eligibility(dest2, purpose2, 14)
            visa_bool = quick_check["visa_required"] or False
        else:
            visa_bool = visa_needed == "Yes"

        checklist = get_document_checklist(dest2, purpose2, visa_bool)

        st.markdown("---")
        st.markdown(f"### Documents for: **{dest2}** · {purpose2}")

        # Always required
        st.markdown('<div class="section-header">✅ Always Required</div>', unsafe_allow_html=True)
        for item in checklist["always_required"]:
            st.markdown(f"""
            <div class="checklist-item checklist-required">
              <span class="check-icon">✅</span>
              <span>{item}</span>
            </div>
            """, unsafe_allow_html=True)

        # Sometimes required
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

        # Important note
        if checklist["important_note"]:
            st.markdown(f'<div class="note-box" style="margin-top:1rem">📌 <strong>Important note for your trip type:</strong><br>{checklist["important_note"]}</div>', unsafe_allow_html=True)

        # Download hint
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
      visa-free to signatory countries for short stays (typically up to 90 days). Over 20 European countries have ratified it,
      including France, Germany, Italy, Spain, Romania, and others.<br><br>
      <strong>The key problem:</strong> Many embassies and border officers are unaware of this treaty, and sometimes give incorrect advice —
      telling CTD holders they need a visa when they legally do not. This is one of the core problems Secure Path is designed to solve.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**What to say if an embassy gives you wrong information:**")
    st.code(
        'I am a holder of a UK Convention Travel Document issued under the 1951 Refugee Convention. '
        'Under the 1959 Council of Europe Agreement on the Abolition of Visas for Refugees '
        '(ETS No. 31), to which [COUNTRY] is a signatory, I am entitled to visa-free entry '
        'for stays of up to 90 days. I respectfully request that this be reviewed.',
        language=None
    )

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:#94A3B8; font-size:0.8rem; padding: 1rem 0;">
      Secure Path · Research Prototype · MMU Business Technology Project 5Z6Z1002 · 2026/27<br>
      This tool does not constitute legal advice. Always verify with official sources before travelling.
    </div>
    """, unsafe_allow_html=True)
