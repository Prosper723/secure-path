"""
Secure Path — Eligibility Engine
Reasoning logic for visa eligibility and document generation.
"""

from data import (
    ETS_31_COUNTRIES, BILATERAL_COUNTRIES,
    DOCUMENT_CHECKLISTS, CTD_INFO
)


def check_eligibility(destination: str, purpose: str, duration_days: int):
    """
    Core eligibility reasoning engine.
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
    }

    # --- Check ETS No. 31 countries ---
    if destination in ETS_31_COUNTRIES:
        info = ETS_31_COUNTRIES[destination]
        allowed_days = info["days"]

        if duration_days <= allowed_days:
            result["visa_required"] = False
            result["verdict"] = "visa_free"
            result["verdict_label"] = "✅ No Visa Required"
            result["legal_basis"] = f"1959 Strasbourg Agreement (ETS No. 31) — {destination} is a signatory state. CTD holders are exempt from visa requirements for stays up to {allowed_days} days."
            result["key_message"] = f"You do not need a visa to travel to {destination} for {duration_days} days. Your Convention Travel Document grants you visa-free access under international treaty law."
            result["warnings"].append("⚠️ Some embassies may incorrectly advise you to obtain a visa. They are legally wrong. If this happens, quote ETS No. 31 directly and request escalation.")
        else:
            result["visa_required"] = True
            result["verdict"] = "visa_required"
            result["verdict_label"] = "⚠️ Visa May Be Required"
            result["legal_basis"] = f"ETS No. 31 covers stays up to {allowed_days} days. Your planned stay of {duration_days} days exceeds this."
            result["key_message"] = f"Your stay exceeds the {allowed_days}-day visa-free limit under ETS No. 31. You will need to apply for a long-stay visa or residence permit from the {destination} embassy."

    # --- Check bilateral agreement countries ---
    elif destination in BILATERAL_COUNTRIES:
        info = BILATERAL_COUNTRIES[destination]
        result["visa_required"] = info["visa_required"]
        result["evisa_required"] = info.get("evisa", False)
        result["evisa_info"] = info.get("evisa_info")

        if not info["visa_required"]:
            result["verdict"] = "visa_free"
            result["verdict_label"] = "✅ No Visa Required"
            result["legal_basis"] = "Bilateral arrangement between UK and destination country."
            result["key_message"] = f"You do not need a visa to travel to {destination} with a Convention Travel Document."
        else:
            result["verdict"] = "visa_required"
            result["verdict_label"] = "🔴 Visa Required"
            result["legal_basis"] = info["notes"]
            result["key_message"] = f"A visa is required to travel to {destination} with a Convention Travel Document. Apply well in advance of your travel date."
            if info.get("evisa"):
                result["warnings"].append(f"🌐 eVisa required — apply online before travelling. {info['evisa_info']}")

    else:
        # Unknown country
        result["verdict"] = "check_required"
        result["verdict_label"] = "❓ Manual Check Required"
        result["visa_required"] = None
        result["legal_basis"] = "This country is not in our current database."
        result["key_message"] = f"We don't have specific information for {destination} yet. Contact the embassy directly or consult the UNHCR travel advisory. Always ask specifically about Convention Travel Document / Refugee Travel Document holders."

    # --- Add purpose-specific note for voluntary work ---
    if purpose == "Voluntary Work / Work Experience":
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

    # Duration-based additions
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

    # Step 1: Check eligibility (done — they're here)
    steps.append({
        "step": 1,
        "title": "Check Your Eligibility",
        "status": "complete",
        "detail": "You've completed this step by using Secure Path.",
        "timeframe": "Now"
    })

    # Step 2: Gather documents
    steps.append({
        "step": 2,
        "title": "Gather Your Documents",
        "status": "action",
        "detail": "Use the document checklist below. Start with your CTD validity — it must be valid for at least 6 months beyond your return date.",
        "timeframe": "4-8 weeks before travel"
    })

    # Step 3: Visa application (if needed)
    if visa_required:
        evisa_text = "Apply online for your eVisa first, then book your embassy appointment if required." if evisa_required else "Book an appointment at the embassy or consulate. Do not travel before your visa is issued."
        steps.append({
            "step": 3,
            "title": "Apply for Your Visa",
            "status": "action",
            "detail": evisa_text,
            "timeframe": "6-10 weeks before travel"
        })

    # Step 4: Travel insurance
    steps.append({
        "step": len(steps) + 1,
        "title": "Purchase Travel Insurance",
        "status": "action",
        "detail": "Ensure your policy covers medical, repatriation, and the specific purpose of your trip (e.g. voluntary work if applicable). Keep a digital and printed copy.",
        "timeframe": "Before booking flights"
    })

    # Step 5: Border crossing prep
    steps.append({
        "step": len(steps) + 1,
        "title": "Prepare for Border Crossing",
        "status": "info",
        "detail": f"At the border, present your CTD and all supporting documents. If asked why you don't have a standard passport, calmly explain you hold a UK Convention Travel Document issued under the 1951 Refugee Convention. {'For eVisa countries, ensure your eVisa is on your phone AND printed — some border officers still ask for paper.' if evisa_required else ''}",
        "timeframe": "Day of travel"
    })

    # Step 6: Return to UK
    steps.append({
        "step": len(steps) + 1,
        "title": "Returning to the UK",
        "status": "info",
        "detail": "Your CTD guarantees your right of return to the UK. At UK Border Force, use the 'Other Documents' lane if eGates don't accept your CTD. The officer will verify your leave to remain status.",
        "timeframe": "On return"
    })

    return steps
