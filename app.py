"""
Secure Path — Main Streamlit Application
GovTech platform for Convention Travel Document holders.
v2.1 — Clean UI + Agentic AI Travel Adviser
"""

import streamlit as st
import sys
import os
import re

sys.path.insert(0, os.path.dirname(__file__))
from engine import check_eligibility, get_document_checklist, get_journey_steps
from data import ALL_COUNTRIES, PURPOSES, CTD_INFO, AI_LEGAL_CONTEXT, ETS_31_COUNTRIES, BILATERAL_COUNTRIES


# ══════════════════════════════════════════════════════════════════════════════
# DEMO AI — defined before tabs
# ══════════════════════════════════════════════════════════════════════════════
def _demo_ai_response(user_input: str, history: list) -> str:
    text = user_input.lower()
    all_history = " ".join([m["content"].lower() for m in history])

    detected_country = None
    for country in list(ETS_31_COUNTRIES.keys()) + list(BILATERAL_COUNTRIES.keys()):
        if country.lower() in text or country.lower() in all_history:
            detected_country = country
            break

    is_paid_work = any(kw in text for kw in [
        "paid internship", "paid work", "job", "salary", "employment",
        "internship", "working", "earning", "stipend", "remuneration"
    ])
    is_unpaid = any(kw in text for kw in ["volunteer", "voluntary", "unpaid", "charity", "ngo", "placement"])
    is_study = any(kw in text for kw in ["study", "university", "masters", "phd", "degree", "student"])
    is_holiday = any(kw in text for kw in ["holiday", "tourism", "tourist", "visit", "vacation", "travelling", "travel"])

    duration_match = re.search(r'(\d+)\s*(day|week|month)', text)
    duration_days = None
    if duration_match:
        num = int(duration_match.group(1))
        unit = duration_match.group(2)
        duration_days = num * 7 if unit == "week" else num * 30 if unit == "month" else num

    is_greeting = any(kw in text for kw in ["hello", "hi", "hey", "what can you"])
    is_just_help = "help" in text and not detected_country and not (is_paid_work or is_unpaid or is_study or is_holiday)
    if is_greeting or is_just_help:
        return (
            "Hi! I help CTD holders navigate visa rules — especially tricky situations like paid internships "
            "in countries that look visa-free on paper but aren't.\n\n"
            "Tell me: **where** are you going, **what for**, and **how long**?"
        )

    if detected_country and detected_country in ETS_31_COUNTRIES and is_paid_work:
        dur_str = f"{duration_days} days" if duration_days else "duration TBC"
        return (
            f"**🔴 Work visa required — here's why:**\n\n"
            f"**{detected_country}** has signed ETS No. 31 (the 1959 Strasbourg Agreement), "
            f"which normally grants CTD holders visa-free entry for up to 90 days.\n\n"
            f"**However — Article 1(2) changes everything for paid work.** "
            f"The visa-free right only applies to *non-gainful* purposes. "
            f"A paid internship is *gainful employment*, so the exemption doesn't apply — even here.\n\n"
            f"**What you need:** A work visa / work permit from the {detected_country} embassy before you travel.\n\n"
            f"**Next steps:**\n"
            f"1. Contact the {detected_country} embassy in London\n"
            f"2. Ask your employer to start sponsorship paperwork (allow 8–12 weeks)\n"
            f"3. Don't book flights until the visa is in hand\n\n"
            f"*Trip: {detected_country} · Paid work · {dur_str}*\n\n"
            f"> ⚠️ Guidance only. Confirm with the {detected_country} embassy before travelling."
        )

    if detected_country and detected_country in ETS_31_COUNTRIES and is_unpaid:
        over = duration_days and duration_days > 90
        dur_str = f"{duration_days} days" if duration_days else "duration TBC"
        over_note = (
            f"\n\n**⚠️ Duration issue:** Your stay of {duration_days} days exceeds the 90-day visa-free limit. "
            f"You'd need a long-stay visa even though the work is unpaid." if over
            else f"\n\n✅ {duration_days} days is within the 90-day limit." if duration_days else ""
        )
        return (
            f"**✅ Good news — your visa-free rights are preserved.**\n\n"
            f"Under ETS No. 31 Article 1(2), unpaid voluntary work is *not* classed as gainful employment. "
            f"Your CTD gives you visa-free entry to **{detected_country}** for up to 90 days.{over_note}\n\n"
            f"**Bring with you:** CTD (6+ months validity), confirmation letter stating the placement is unpaid, "
            f"proof of funds, accommodation, and travel insurance.\n\n"
            f"> ⚠️ Guidance only. Verify with the {detected_country} embassy before travelling."
        )

    if detected_country and detected_country in ETS_31_COUNTRIES:
        over = duration_days and duration_days > 90
        dur_str = f"{duration_days} days" if duration_days else None
        if over:
            result_line = f"**⚠️ Long-stay visa required.** Your stay of {duration_days} days exceeds the 90-day limit under ETS No. 31."
        else:
            result_line = f"**✅ No visa required** for this trip."

        return (
            f"{result_line}\n\n"
            f"**{detected_country}** has ratified ETS No. 31 (1959 Strasbourg Agreement), "
            f"granting CTD holders visa-free entry for non-gainful purposes up to 90 days."
            + (f" Your {dur_str} stay is within that limit." if dur_str and not over else "")
            + "\n\n**One thing to confirm:** Is any part of this trip **paid work or a paid internship**? "
            "If yes, the answer changes completely — paid work requires a work visa even in ETS No. 31 countries (Article 1(2)).\n\n"
            "> ⚠️ Some embassies incorrectly require visas for non-gainful ETS 31 travel. If this happens, cite ETS No. 31 directly."
        )

    if detected_country and detected_country in BILATERAL_COUNTRIES:
        info = BILATERAL_COUNTRIES[detected_country]
        if info["visa_required"]:
            evisa_note = f"\n\n🌐 **eVisa available:** {info['evisa_info']}" if info.get("evisa") else ""
            return (
                f"**🔴 Visa required for {detected_country}.**\n\n"
                f"{info['notes']}{evisa_note}\n\n"
                f"Apply at least 8 weeks before travel. CTD must be valid for 6+ months beyond your return date.\n\n"
                f"> ⚠️ Guidance only. Verify with the {detected_country} embassy."
            )
        else:
            return (
                f"**✅ No visa required for {detected_country}.**\n\n"
                f"{info['notes']}\n\n"
                f"> ⚠️ Guidance only. Confirm requirements before travelling."
            )

    if is_study and detected_country:
        return (
            f"**📚 Study in {detected_country} — student visa likely required.**\n\n"
            f"Even in ETS No. 31 countries, formal study (enrolling at a university) usually requires a student visa regardless of duration.\n\n"
            f"Contact the {detected_country} embassy or your institution's international office for exact requirements. "
            f"You'll typically need: student visa, enrolment letter, proof of funds, accommodation, and insurance.\n\n"
            f"> ⚠️ Visa rules vary by country and course type."
        )

    missing = []
    if not detected_country:
        missing.append("destination country")
    if not (is_paid_work or is_unpaid or is_study or is_holiday):
        missing.append("purpose of your trip (paid work, volunteer, tourism, study?)")
    if not duration_days:
        missing.append("how long you plan to stay")

    if missing:
        return (
            "I need a bit more to give you an accurate answer:\n\n"
            + "\n".join(f"- **{m}**" for m in missing)
            + "\n\nExample: *'I'm going to Romania for a paid 3-month internship'* "
            "or *'visiting France for 2 weeks as a tourist'*."
        )

    return (
        "Could you clarify the **purpose** of your trip?\n\n"
        "- Paid work / internship?\n"
        "- Unpaid volunteering?\n"
        "- Tourism / holiday?\n"
        "- Study?\n\n"
        "This is the most important factor — especially whether any work is paid."
    )


# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Secure Path",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── GLOBAL CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* ── Hero ── */
  .hero {
    background: linear-gradient(135deg, #0A1628 0%, #1a3a6b 60%, #2563EB 100%);
    padding: 2.5rem 2.5rem 2rem;
    border-radius: 14px;
    margin-bottom: 1.5rem;
    color: white;
  }
  .hero-badge {
    display: inline-block;
    background: rgba(245,158,11,0.2);
    border: 1px solid #F59E0B;
    color: #FCD34D;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-bottom: 0.8rem;
  }
  .hero h1 { font-size: 2.4rem; font-weight: 700; margin: 0; letter-spacing: -0.5px; }
  .hero .subtitle { font-size: 1rem; opacity: 0.8; margin-top: 0.4rem; font-weight: 300; }
  .hero .disclaimer {
    background: rgba(255,255,255,0.08);
    border-left: 3px solid #F59E0B;
    padding: 0.5rem 0.9rem;
    border-radius: 0 8px 8px 0;
    font-size: 0.78rem;
    opacity: 0.85;
    margin-top: 1.2rem;
  }

  /* ── Verdict cards ── */
  .verdict-card {
    padding: 1.4rem 1.6rem;
    border-radius: 12px;
    margin-bottom: 1rem;
  }
  .vc-free    { background:#ECFDF5; border-left:5px solid #059669; }
  .vc-req     { background:#FEF2F2; border-left:5px solid #DC2626; }
  .vc-check   { background:#FFFBEB; border-left:5px solid #D97706; }
  .vc-title   { font-size:1.35rem; font-weight:700; margin-bottom:0.3rem; }
  .vc-free  .vc-title { color:#065F46; }
  .vc-req   .vc-title { color:#991B1B; }
  .vc-check .vc-title { color:#92400E; }
  .vc-msg { font-size:0.93rem; color:#374151; line-height:1.55; }

  /* ── Alert / info strips — ONE style, colour via modifier ── */
  .alert {
    display:flex; align-items:flex-start; gap:0.7rem;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    font-size: 0.88rem;
    line-height: 1.55;
    margin: 0.5rem 0;
  }
  .alert-red    { background:#FEF2F2; border:1px solid #FECACA; color:#7F1D1D; }
  .alert-amber  { background:#FFFBEB; border:1px solid #FDE68A; color:#78350F; }
  .alert-blue   { background:#EFF6FF; border:1px solid #BFDBFE; color:#1E3A8A; }
  .alert-green  { background:#ECFDF5; border:1px solid #A7F3D0; color:#064E3B; }
  .alert-icon   { font-size:1rem; flex-shrink:0; margin-top:1px; }

  /* ── Checklist ── */
  .cl-item {
    display:flex; align-items:flex-start; gap:0.6rem;
    padding:0.65rem 0.9rem; margin:0.25rem 0;
    border-radius:8px; font-size:0.9rem; line-height:1.5;
  }
  .cl-req { background:#F0FDF4; border:1px solid #BBF7D0; color:#14532D; }
  .cl-opt { background:#F8FAFC; border:1px solid #E2E8F0; color:#475569; }

  /* ── Steps ── */
  .step {
    display:flex; align-items:flex-start; gap:1rem;
    padding:1rem 1.2rem; margin:0.4rem 0;
    border-radius:10px; border:1px solid #E2E8F0; background:white;
  }
  .step-num {
    width:34px; height:34px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-weight:700; font-size:0.88rem; flex-shrink:0;
  }
  .s-done .step-num { background:#059669; color:white; }
  .s-act  .step-num { background:#2563EB; color:white; }
  .s-info .step-num { background:#64748B; color:white; }
  .step-title { font-weight:600; font-size:0.92rem; color:#1E293B; }
  .step-time  { font-size:0.75rem; color:#94A3B8; font-weight:500; margin:1px 0 3px; }
  .step-body  { font-size:0.86rem; color:#475569; line-height:1.5; }

  /* ── Section label ── */
  .sec-label {
    font-size:0.7rem; font-weight:700; letter-spacing:1px;
    text-transform:uppercase; color:#2563EB;
    padding-bottom:0.5rem; border-bottom:2px solid #DBEAFE;
    margin:1.5rem 0 0.9rem;
  }

  /* ── CTD facts ── */
  .fact {
    background:white; border:1px solid #E2E8F0;
    border-radius:8px; padding:0.7rem 1rem;
    margin:0.3rem 0; font-size:0.87rem; color:#334155;
  }
  .fact strong { color:#0A1628; }

  /* ── AI tab ── */
  .ai-header {
    display:flex; align-items:center; justify-content:space-between;
    padding:0.8rem 0 0.6rem; border-bottom:1px solid #E2E8F0; margin-bottom:0.8rem;
  }
  .ai-header-title { font-size:1rem; font-weight:600; color:#0A1628; }
  .demo-pill {
    background:#FEF3C7; border:1px solid #FCD34D;
    color:#92400E; font-size:0.72rem; font-weight:600;
    padding:3px 10px; border-radius:20px; letter-spacing:0.3px;
  }
  .live-pill {
    background:#ECFDF5; border:1px solid #6EE7B7;
    color:#065F46; font-size:0.72rem; font-weight:600;
    padding:3px 10px; border-radius:20px; letter-spacing:0.3px;
  }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] { gap:0.4rem; border-bottom:2px solid #E2E8F0; }
  .stTabs [data-baseweb="tab"] { font-weight:500; font-size:0.88rem; padding:0.5rem 1.1rem; border-radius:8px 8px 0 0; }
</style>
""", unsafe_allow_html=True)


# ─── HERO HEADER ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-badge">🛡️ RESEARCH PROTOTYPE · MMU 5Z6Z1002</div>
  <h1>Secure Path</h1>
  <div class="subtitle">Visa eligibility &amp; document guidance for UK Convention Travel Document holders</div>
  <div class="disclaimer">
    ⚠️ <strong>Research prototype.</strong>
    This tool is for academic demonstration only. It does not constitute legal advice.
    Always verify requirements with the official embassy before travelling.
  </div>
</div>
""", unsafe_allow_html=True)


# ─── TABS ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍  Eligibility Checker",
    "📋  Document Checklist",
    "ℹ️  About My CTD",
    "🤖  AI Travel Adviser",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ELIGIBILITY CHECKER
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="sec-label">Check your eligibility</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        destination = st.selectbox("🌍 Destination country", ["Select a country…"] + ALL_COUNTRIES)
    with col2:
        purpose = st.selectbox("✈️ Purpose of travel", PURPOSES)
    with col3:
        duration = st.number_input("📅 Days", min_value=1, max_value=365, value=14)

    st.markdown("<br>", unsafe_allow_html=True)
    check_btn = st.button("Check My Eligibility →", type="primary", use_container_width=True)

    if check_btn and destination != "Select a country…":
        result = check_eligibility(destination, purpose, duration)

        st.markdown("---")

        vc_class = {"visa_free": "vc-free", "visa_required": "vc-req", "check_required": "vc-check"}[result["verdict"]]
        st.markdown(f"""
        <div class="verdict-card {vc_class}">
          <div class="vc-title">{result['verdict_label']}</div>
          <div class="vc-msg">{result['key_message']}</div>
        </div>
        """, unsafe_allow_html=True)

        if result.get("article_1_2_applies"):
            st.markdown("""
            <div class="alert alert-red">
              <span class="alert-icon">📌</span>
              <span><strong>ETS No. 31 Article 1(2) — Paid Work Rule:</strong>
              The Strasbourg Agreement's visa-free provisions cover <em>non-gainful purposes only</em>.
              Paid work or internships count as gainful employment, so the exemption does not apply —
              even in ETS No. 31 signatory countries. A work visa is always required for paid roles.</span>
            </div>
            """, unsafe_allow_html=True)

        if result["legal_basis"]:
            st.markdown(f'<div class="alert alert-blue"><span class="alert-icon">📜</span><span><strong>Legal basis:</strong> {result["legal_basis"]}</span></div>', unsafe_allow_html=True)

        if result["evisa_required"] and result["evisa_info"]:
            st.markdown(f'<div class="alert alert-amber"><span class="alert-icon">🌐</span><span><strong>eVisa required:</strong> {result["evisa_info"]}</span></div>', unsafe_allow_html=True)

        if result["important_note"]:
            st.markdown(f'<div class="alert alert-amber"><span class="alert-icon">📌</span><span>{result["important_note"]}</span></div>', unsafe_allow_html=True)

        for w in result["warnings"]:
            st.markdown(f'<div class="alert alert-amber"><span class="alert-icon">⚠️</span><span>{w}</span></div>', unsafe_allow_html=True)

        st.markdown('<div class="sec-label">Your step-by-step journey plan</div>', unsafe_allow_html=True)
        steps = get_journey_steps(destination, purpose, result["visa_required"] or False, result["evisa_required"])

        for step in steps:
            s_class = {"complete": "s-done", "action": "s-act", "info": "s-info"}.get(step["status"], "s-info")
            st.markdown(f"""
            <div class="step {s_class}">
              <div class="step-num">{step['step']}</div>
              <div>
                <div class="step-title">{step['title']}</div>
                <div class="step-time">⏱ {step['timeframe']}</div>
                <div class="step-body">{step['detail']}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        if result["article_1_2_applies"] or result["verdict"] == "check_required":
            st.markdown("""
            <div class="alert alert-blue" style="margin-top:1rem">
              <span class="alert-icon">💬</span>
              <span>Complex situation? Try the <strong>🤖 AI Travel Adviser</strong> tab for personalised step-by-step guidance.</span>
            </div>
            """, unsafe_allow_html=True)

    elif check_btn:
        st.warning("Please select a destination country first.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DOCUMENT CHECKLIST
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="sec-label">Generate your document checklist</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        dest2 = st.selectbox("🌍 Destination", ["Select a country…"] + ALL_COUNTRIES, key="dest2")
    with c2:
        purpose2 = st.selectbox("✈️ Purpose", PURPOSES, key="purpose2")
    with c3:
        visa_needed = st.selectbox("🔑 Visa needed?", ["Not sure", "Yes", "No"], key="visa2")

    gen_btn = st.button("Generate My Checklist →", type="primary", use_container_width=True)

    if gen_btn and dest2 != "Select a country…":
        visa_bool = (check_eligibility(dest2, purpose2, 14)["visa_required"] or False) if visa_needed == "Not sure" else (visa_needed == "Yes")
        checklist = get_document_checklist(dest2, purpose2, visa_bool)

        st.markdown("---")
        st.markdown(f"**Documents for {dest2} — {purpose2}**")

        st.markdown('<div class="sec-label">Always required</div>', unsafe_allow_html=True)
        for item in checklist["always_required"]:
            st.markdown(f'<div class="cl-item cl-req"><span>✅</span><span>{item}</span></div>', unsafe_allow_html=True)

        if checklist["sometimes_required"]:
            st.markdown('<div class="sec-label">May also be required</div>', unsafe_allow_html=True)
            st.caption("Confirm with the embassy which of these apply to your specific situation.")
            for item in checklist["sometimes_required"]:
                st.markdown(f'<div class="cl-item cl-opt"><span>📎</span><span>{item}</span></div>', unsafe_allow_html=True)

        if checklist["important_note"]:
            st.markdown(f'<div class="alert alert-amber" style="margin-top:1rem"><span class="alert-icon">📌</span><span>{checklist["important_note"]}</span></div>', unsafe_allow_html=True)

        checklist_text = (
            f"SECURE PATH — Document Checklist\n{'='*50}\n"
            f"Destination: {dest2}\nPurpose: {purpose2}\n\nALWAYS REQUIRED:\n"
            + "".join(f"  {i}. {x}\n" for i, x in enumerate(checklist["always_required"], 1))
            + ("\nMAY ALSO BE REQUIRED:\n" + "".join(f"  {i}. {x}\n" for i, x in enumerate(checklist["sometimes_required"], 1)) if checklist["sometimes_required"] else "")
            + "\n⚠️ Research prototype. Verify with the official embassy before travelling."
        )
        st.download_button("⬇️ Download Checklist (.txt)", checklist_text,
                           file_name=f"SecurePath_Checklist_{dest2.replace(' ', '_')}.txt", mime="text/plain")

    elif gen_btn:
        st.warning("Please select a destination country first.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ABOUT MY CTD
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="sec-label">Understanding your Convention Travel Document</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**What is it?**")
        st.markdown("""
        <div class="fact">
          The <strong>Convention Travel Document (CTD)</strong> — also known as a Refugee Travel Document or Blue Travel Document —
          is issued by the UK Home Office to people granted refugee status or humanitarian protection.
          It is legally recognised under the <strong>1951 UN Refugee Convention, Article 28</strong>.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Key facts**")
        for label, value in [
            ("Valid for", "10 years (adults) / 5 years (under 16)"),
            ("Issued by", "UK Home Office"),
            ("Legal basis", "1951 UN Refugee Convention, Article 28"),
            ("Also called", "Refugee Travel Document, Blue Travel Document"),
        ]:
            st.markdown(f'<div class="fact"><strong>{label}:</strong> {value}</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown("**Your rights**")
        for right in CTD_INFO["key_rights"]:
            st.markdown(f'<div class="cl-item cl-req"><span>✅</span><span>{right}</span></div>', unsafe_allow_html=True)

        st.markdown("**Important limitations**")
        for limit in CTD_INFO["key_limitations"]:
            st.markdown(f'<div class="cl-item cl-opt"><span>⚠️</span><span>{limit}</span></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="sec-label">The 1959 Strasbourg Agreement — ETS No. 31</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="alert alert-blue">
      <span class="alert-icon">📜</span>
      <span>
        <strong>ETS No. 31</strong> stands for <em>European Treaty Series No. 31</em> — the official Council of Europe
        reference number for the <strong>1959 Agreement on the Abolition of Visas for Refugees</strong> (also called the
        Strasbourg Agreement). Under this treaty, 20 signatory countries grant CTD holders visa-free entry for
        non-gainful purposes (tourism, family visits, voluntary work) for stays up to 90 days.
        <br><br>
        <strong>⚠️ Critical nuance — Article 1(2):</strong> The visa-free right applies to
        <em>non-gainful purposes only</em>. A paid internship or job is gainful employment —
        so even in a signatory country, you still need a work visa for paid roles.
      </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**If an embassy incorrectly requires a visa for a non-gainful visit, use this script:**")
    st.code(
        "I hold a UK Convention Travel Document issued under the 1951 Refugee Convention. "
        "Under ETS No. 31 (European Treaty Series No. 31 — the 1959 Council of Europe Agreement "
        "on the Abolition of Visas for Refugees), to which [COUNTRY] is a signatory, I am entitled "
        "to visa-free entry for non-gainful purposes for stays up to 90 days. "
        "I respectfully request that this be reviewed.",
        language=None
    )

    st.markdown("---")
    st.markdown('<div style="text-align:center;color:#94A3B8;font-size:0.78rem;padding:0.8rem 0">Secure Path · Research Prototype · MMU 5Z6Z1002 · 2026/27 · Not legal advice</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — AI TRAVEL ADVISER
# ══════════════════════════════════════════════════════════════════════════════
with tab4:

    # ── API key setup ──────────────────────────────────────────────────────
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key and "openai_key" in st.session_state:
        api_key = st.session_state["openai_key"]

    use_live_ai = bool(api_key)
    mode_pill = '<span class="live-pill">🟢 Live AI</span>' if use_live_ai else '<span class="demo-pill">⚙️ Demo Mode</span>'

    # ── Clean header ──────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="ai-header">
      <span class="ai-header-title">🤖 AI Travel Adviser</span>
      {mode_pill}
    </div>
    """, unsafe_allow_html=True)

    if not use_live_ai:
        with st.expander("🔑 Add OpenAI API key to enable live AI", expanded=False):
            st.caption("Your key is never stored — it only lives in this browser session.")
            entered_key = st.text_input("API Key", type="password", placeholder="sk-...")
            if entered_key:
                st.session_state["openai_key"] = entered_key
                api_key = entered_key
                use_live_ai = True
                st.success("✅ Live AI enabled.")

    # ── Chat history init ─────────────────────────────────────────────────
    if "ai_messages" not in st.session_state:
        st.session_state["ai_messages"] = [{
            "role": "assistant",
            "content": (
                "Hi! I'm your Secure Path AI Adviser for UK Convention Travel Document holders.\n\n"
                "Tell me where you're going, what for, and how long — I'll reason through the visa rules for your specific situation."
            )
        }]

    # ── Chat display ──────────────────────────────────────────────────────
    for msg in st.session_state["ai_messages"]:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

    # ── Input ─────────────────────────────────────────────────────────────
    user_input = st.chat_input("Where are you going and what for?")

    if user_input:
        st.session_state["ai_messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking…"):
                if use_live_ai:
                    try:
                        from openai import OpenAI
                        client = OpenAI(api_key=api_key)
                        system_prompt = f"""You are the Secure Path AI Travel Adviser for UK Convention Travel Document (CTD) holders.

Give personalised, legally accurate travel guidance. Reason through situations step by step.

LEGAL KNOWLEDGE BASE:
{AI_LEGAL_CONTEXT}

RULES:
1. Always check PURPOSE (paid/unpaid work, tourism, study) and DURATION — these determine the answer.
2. ETS No. 31 visa-free rights apply ONLY to non-gainful purposes (Article 1(2)). Paid work = visa required.
3. Be concise. Bold key conclusions. Use ✅ visa-free, 🔴 visa required, ⚠️ warning.
4. Cite the specific legal basis (e.g. "ETS No. 31 Article 1(2)").
5. End every visa-required answer with: "⚠️ Guidance only. Verify with the embassy before booking."
6. Never invent rules not in your knowledge base."""

                        messages_for_api = [{"role": "system", "content": system_prompt}]
                        for msg in st.session_state["ai_messages"]:
                            messages_for_api.append({"role": msg["role"], "content": msg["content"]})

                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=messages_for_api,
                            max_tokens=600,
                            temperature=0.3,
                        )
                        ai_response = response.choices[0].message.content

                    except ImportError:
                        ai_response = "⚠️ OpenAI library not installed. Run `pip install openai` and restart."
                    except Exception as e:
                        ai_response = f"⚠️ AI error: {e}\n\nPlease try the Eligibility Checker tab instead."
                else:
                    ai_response = _demo_ai_response(user_input, st.session_state["ai_messages"])

                st.markdown(ai_response)

        st.session_state["ai_messages"].append({"role": "assistant", "content": ai_response})

    # ── Clear button ──────────────────────────────────────────────────────
    col_c, _ = st.columns([1, 5])
    with col_c:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state["ai_messages"] = [{
                "role": "assistant",
                "content": "Chat cleared. Where are you going and what for?"
            }]
            st.rerun()
