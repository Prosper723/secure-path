"""
Secure Path — Eligibility Engine
Reasoning logic for visa eligibility and document generation.

Key legal rule encoded here:
ETS No. 31 Article 1(2) — visa-free only for NON-GAINFUL purposes.
Paid internships / employment = gainful → visa required even in ETS 31 countries.
"""

from data import (
    ETS_31_COUNTRIES, BILATERAL_COUNTRIES,
    DOCUMENT_CHECKLISTS, CTD_INFO
)

# Purposes that constitute "gainful employment" under ETS No. 31 Article 1(2)
GAINFUL_PURPOSES = {"Paid Work / Internship"}

# Purposes that are explicitly non-gainful (visa-free preserved under ETS 31)
NON_GAINFUL_PURPOSES = {
    "Tourism / Holiday",
    "Visiting Family / Friends",
    "Voluntary Work / Work Experience",
    "Business / Conference",  # attending, not working; depends on nature
}


def check_eligibility(destination: str, purpose: str, duration_days: int):
    """
    Core eligibility reasoning engine.

    ETS No. 31 Article 1(2) awareness:
    - If purpose is gainful employment (paid work/internship), ETS 31 visa-free does NOT apply.
    - If stay exceeds 90 days, ETS 31 visa-free does NOT apply.
    - Both conditions independently trigger visa requirement.

    Returns a structured result dict.
    """
    result = {
        "destination": destination,
        "purpose": purpose,
        "duration_days": duration_days,
        "visa_required": None,
        "verdict": None,           # "visa_free" | "visa_required" | "check_required"
        "verdict_label": None,
        "legal_basis": None,
        "key_message": None,
        "warnings": [],
        "evisa_required": False,
        "evisa_info": None,
        "important_note": None,
        "article_1_2_applies": False,  # True when ETS 31 visa-free is blocked by gainful employment
    }

    is_gainful = purpose in GAINFUL_PURPOSES

    # ── Check ETS No. 31 countries ───────────────────────────────────────────
    if destination in ETS_31_COUNTRIES:
        info = ETS_31_COUNTRIES[destination]
        allowed_days = info["days"]

        if is_gainful:
            # Article 1(2): paid work = gainful employment = visa required
            result["visa_required"] = True
            result["verdict"] = "visa_required"
            result["verdict_label"] = "🔴 Work Visa Required"
            result["article_1_2_applies"] = True
            result["legal_basis"] = (
                f"ETS No. 31 Article 1(2) — {destination} is an ETS No. 31 signatory, "
                f"but the visa-free provisions apply only to non-gainful purposes. "
                f"Paid work/internships constitute gainful employment and fall outside the treaty's protection."
            )
            result["key_message"] = (
                f"⚠️ Even though {destination} is an ETS No. 31 signatory country, "
                f"you CANNOT rely on visa-free entry for a paid internship or paid work. "
                f"Paid employment is 'gainful' under Article 1(2) of the treaty, which means the "
                f"visa-free exemption does not apply. You must apply for a work visa before travelling."
            )
            result["important_note"] = (
                "This is a very common mistake. Many CTD holders assume that ETS No. 31 covers all "
                "travel to signatory countries — but it explicitly excludes gainful employment. "
                "Travelling to work without a work visa could result in refusal of entry or deportation."
            )

        elif duration_days > allowed_days:
            # Duration exceeds visa-free limit
            result["visa_required"] = True
            result["verdict"] = "visa_required"
            result["verdict_label"] = "⚠️ Long-Stay Visa Required"
            result["legal_basis"] = (
                f"ETS No. 31 covers stays up to {allowed_days} days. "
                f"Your planned stay of {duration_days} days exceeds this limit."
            )
            result["key_message"] = (
                f"Your stay of {duration_days} days exceeds the {allowed_days}-day visa-free limit "
                f"under ETS No. 31. You will need to apply for a long-stay visa or residence permit "
                f"from the {destination} embassy before travelling."
            )

        else:
            # Genuinely visa-free
            result["visa_required"] = False
            result["verdict"] = "visa_free"
            result["verdict_label"] = "✅ No Visa Required"
            result["legal_basis"] = (
                f"1959 Strasbourg Agreement (ETS No. 31) — {destination} is a signatory state. "
                f"CTD holders are exempt from visa requirements for non-gainful stays up to {allowed_days} days."
            )
            result["key_message"] = (
                f"You do not need a visa to travel to {destination} for {duration_days} days. "
                f"Your Convention Travel Document grants you visa-free access under international treaty law."
            )
            result["warnings"].append(
                "⚠️ Some embassies may incorrectly advise you to obtain a visa. "
                "They are legally wrong. If this happens, quote ETS No. 31 directly and request escalation."
            )

    # ── Check bilateral agreement countries ──────────────────────────────────
    elif destination in BILATERAL_COUNTRIES:
        info = BILATERAL_COUNTRIES[destination]
        result["visa_required"] = info["visa_required"]
        result["evisa_required"] = info.get("evisa", False)
        result["evisa_info"] = info.get("evisa_info")

        if not info["visa_required"]:
            result["verdict"] = "visa_free"
            result["verdict_label"] = "✅ No Visa Required"
            result["legal_basis"] = "Bilateral arrangement between UK and destination country."
            result["key_message"] = (
                f"You do not need a visa to travel to {destination} with a Convention Travel Document."
            )
            # Even in bilateral visa-free countries, work still requires a work visa
            if is_gainful:
                result["warnings"].append(
                    "⚠️ Note: While short tourist visits may be visa-free, "
                    "paid work requires a separate work visa regardless of any bilateral arrangement."
                )
        else:
            result["verdict"] = "visa_required"
            result["verdict_label"] = "🔴 Visa Required"
            result["legal_basis"] = info["notes"]
            result["key_message"] = (
                f"A visa is required to travel to {destination} with a Convention Travel Document. "
                f"Apply well in advance of your travel date."
            )
            if info.get("evisa"):
                result["warnings"].append(
                    f"🌐 eVisa required — apply online before travelling. {info['evisa_info']}"
                )

    else:
        # Unknown country
        result["verdict"] = "check_required"
        result["verdict_label"] = "❓ Manual Check Required"
        result["visa_required"] = None
        result["legal_basis"] = "This country is not in our current database."
        result["key_message"] = (
            f"We don't have specific information for {destination} yet. "
            f"Contact the embassy directly or consult the UNHCR travel advisory. "
            f"Always ask specifically about Convention Travel Document / Refugee Travel Document holders."
        )

    # ── Add purpose-specific note for voluntary work ─────────────────────────
    if purpose == "Voluntary Work / Work Experience" and destination in ETS_31_COUNTRIES:
        result["important_note"] = (
            "Under Article 1(2) of ETS No. 31, unpaid voluntary work does NOT count as 'gainful employment'. "
            "Your visa-free rights are fully preserved even if you are doing volunteer work. "
            "If an embassy questions this, reference ETS No. 31 Article 1(2) directly."
        )

    return result


def get_document_checklist(destination: str, purpose: str, visa_required: bool):
    """
    Generate a personalised document checklist based on destination, purpose, and visa status.
    """
    base_checklist = DOCUMENT_CHECKLISTS.get(purpose, DOCUMENT_CHECKLISTS["Tourism / Holiday"])

    always = list(base_checklist["always_required"])
    sometimes = list(base_checklist.get("sometimes_required", []))
    important_note = base_checklist.get("important_note", None)

    # Add visa-specific docs if required
    if visa_required:
        if "Visa application form (if destination requires a visa)" in sometimes:
            sometimes.remove("Visa application form (if destination requires a visa)")
        always.append(f"Completed visa application form for {destination}")
        always.append("Visa fee payment (check current fee on embassy website)")
        always.append("Original CTD + 1 clear photocopy of the bio-data page")

    # Country-specific additions
    if destination in ["United States"]:
        sometimes.append("DS-160 online visa application (complete before your embassy appointment)")
        sometimes.append("Appointment confirmation letter from the US Embassy")

    if destination in ["Canada"]:
        sometimes.append("Biometrics appointment at a Visa Application Centre (VAC)")

    if destination in ["Australia", "New Zealand"]:
        sometimes.append("Health examination by a panel physician (required for stays over 3 months)")

    return {
        "always_required": always,
        "sometimes_required": sometimes,
        "important_note": important_note,
    }


def get_journey_steps(destination: str, purpose: str, visa_required: bool, evisa_required: bool):
    """
    Generate a step-by-step Walking Border journey plan.
    """
    steps = []

    steps.append({
        "step": 1,
        "title": "Check Your Eligibility",
        "status": "complete",
        "detail": "You've completed this step by using Secure Path.",
        "timeframe": "Now"
    })

    steps.append({
        "step": 2,
        "title": "Gather Your Documents",
        "status": "action",
        "detail": "Use the document checklist below. Start with your CTD validity — it must be valid for at least 6 months beyond your return date.",
        "timeframe": "4-8 weeks before travel"
    })

    if visa_required:
        evisa_text = (
            "Apply online for your eVisa first, then book your embassy appointment if required."
            if evisa_required else
            "Book an appointment at the embassy or consulate. Do not travel before your visa is issued."
        )
        if purpose == "Paid Work / Internship":
            evisa_text = (
                "Apply for a work visa / work permit from the destination country's embassy. "
                "Your employer may need to sponsor your application. Do not start work before the visa is issued."
            )
        steps.append({
            "step": 3,
            "title": "Apply for Your Visa",
            "status": "action",
            "detail": evisa_text,
            "timeframe": "8-12 weeks before travel"
        })

    steps.append({
        "step": len(steps) + 1,
        "title": "Purchase Travel Insurance",
        "status": "action",
        "detail": "Ensure your policy covers medical, repatriation, and the specific purpose of your trip (e.g. work-related cover if doing paid or voluntary work). Keep a digital and printed copy.",
        "timeframe": "Before booking flights"
    })

    steps.append({
        "step": len(steps) + 1,
        "title": "Prepare for Border Crossing",
        "status": "info",
        "detail": (
            f"At the border, present your CTD and all supporting documents. "
            f"If asked why you don't have a standard passport, calmly explain you hold a UK Convention Travel Document "
            f"issued under the 1951 Refugee Convention. "
            f"{'For eVisa countries, ensure your eVisa is on your phone AND printed — some border officers still ask for paper. ' if evisa_required else ''}"
        ),
        "timeframe": "Day of travel"
    })

    steps.append({
        "step": len(steps) + 1,
        "title": "Returning to the UK",
        "status": "info",
        "detail": "Your CTD guarantees your right of return to the UK. At UK Border Force, use the 'Other Documents' lane if eGates don't accept your CTD. The officer will verify your leave to remain status.",
        "timeframe": "On return"
    })

    return steps
