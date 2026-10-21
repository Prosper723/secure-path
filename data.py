"""
Secure Path — Eligibility & Document Data
Convention Travel Document (CTD) rules based on:
- 1959 Strasbourg Agreement (ETS No. 31)
- Individual country bilateral arrangements
- UK Home Office guidance

Legal intelligence layer for Agentic AI Adviser
"""

# Countries that have ratified ETS No. 31 (Strasbourg Agreement 1959)
# CRITICAL: ETS No. 31 Article 1(2) — visa-free only applies to NON-GAINFUL purposes.
# Paid work/internships = gainful employment = visa required even in ETS 31 countries.
ETS_31_COUNTRIES = {
    "Belgium": {"days": 90, "notes": "Ratified 1960. No visa required for stays up to 90 days for non-gainful purposes."},
    "Denmark": {"days": 90, "notes": "Ratified 1966. No visa required for stays up to 90 days for non-gainful purposes."},
    "France": {"days": 90, "notes": "Ratified 1954. No visa required for stays up to 90 days for non-gainful purposes."},
    "Germany": {"days": 90, "notes": "Ratified 1954. No visa required for stays up to 90 days for non-gainful purposes."},
    "Iceland": {"days": 90, "notes": "Ratified 1955. No visa required for stays up to 90 days for non-gainful purposes."},
    "Ireland": {"days": 90, "notes": "Ratified 1961. No visa required for stays up to 90 days for non-gainful purposes."},
    "Italy": {"days": 90, "notes": "Ratified 1954. No visa required for stays up to 90 days for non-gainful purposes."},
    "Luxembourg": {"days": 90, "notes": "Ratified 1960. No visa required for stays up to 90 days for non-gainful purposes."},
    "Netherlands": {"days": 90, "notes": "Ratified 1956. No visa required for stays up to 90 days for non-gainful purposes."},
    "Norway": {"days": 90, "notes": "Ratified 1955. No visa required for stays up to 90 days for non-gainful purposes."},
    "Portugal": {"days": 90, "notes": "Ratified 1976. No visa required for stays up to 90 days for non-gainful purposes."},
    "Romania": {"days": 90, "notes": "Ratified 1999. No visa required for stays up to 90 days for non-gainful purposes. Note: embassies sometimes incorrectly advise otherwise — your rights are legally protected under ETS No. 31."},
    "Spain": {"days": 90, "notes": "Ratified 1978. No visa required for stays up to 90 days for non-gainful purposes."},
    "Sweden": {"days": 90, "notes": "Ratified 1954. No visa required for stays up to 90 days for non-gainful purposes."},
    "Switzerland": {"days": 90, "notes": "Ratified 1954. No visa required for stays up to 90 days for non-gainful purposes."},
    "United Kingdom": {"days": 90, "notes": "As issuing country — right of return guaranteed."},
    "Austria": {"days": 90, "notes": "Ratified 1974. No visa required for stays up to 90 days for non-gainful purposes."},
    "Finland": {"days": 90, "notes": "Ratified 1990. No visa required for stays up to 90 days for non-gainful purposes."},
    "Greece": {"days": 90, "notes": "Ratified 1960. No visa required for stays up to 90 days for non-gainful purposes."},
    "Turkey": {"days": 90, "notes": "Ratified 1961. No visa required for stays up to 90 days for non-gainful purposes."},
}

# Countries with separate bilateral agreements or arrangements
BILATERAL_COUNTRIES = {
    "Canada": {
        "visa_required": True,
        "notes": "Visa required. CTD holders must apply for a Temporary Resident Visa. Canada does not recognise ETS No. 31.",
        "evisa": True,
        "evisa_info": "Apply online at canada.ca/en/immigration-refugees-citizenship. Biometric data required at a visa application centre."
    },
    "United States": {
        "visa_required": True,
        "notes": "Visa required. CTD holders must apply for a B1/B2 visitor visa at a US Embassy. The Visa Waiver Programme (ESTA) does not apply to CTD holders.",
        "evisa": False,
        "evisa_info": None
    },
    "Australia": {
        "visa_required": True,
        "notes": "Visa required. Apply for a Visitor Visa (subclass 600). The eVisitor and ETA programmes are not available to CTD holders.",
        "evisa": True,
        "evisa_info": "Apply via immi.homeaffairs.gov.au. Processing can take 4-6 weeks."
    },
    "New Zealand": {
        "visa_required": True,
        "notes": "Visa required. Apply for a Visitor Visa at Immigration New Zealand.",
        "evisa": True,
        "evisa_info": "Apply via immigration.govt.nz. Apply at least 6 weeks before travel."
    },
    "Japan": {
        "visa_required": True,
        "notes": "Visa required. Apply at the Japanese Embassy in London.",
        "evisa": False,
        "evisa_info": None
    },
    "South Korea": {
        "visa_required": True,
        "notes": "Visa required. Apply at the Korean Embassy in London.",
        "evisa": False,
        "evisa_info": None
    },
    "UAE": {
        "visa_required": True,
        "notes": "Visa required. CTD holders cannot obtain a visa on arrival. Apply in advance through an authorised UAE travel agent or airline.",
        "evisa": True,
        "evisa_info": "Apply via icp.gov.ae or through your airline. Most airlines servicing UAE routes can arrange this."
    },
    "Morocco": {
        "visa_required": False,
        "notes": "No visa required for CTD holders for stays up to 90 days under a bilateral arrangement.",
        "evisa": False,
        "evisa_info": None
    },
    "Tunisia": {
        "visa_required": False,
        "notes": "No visa required for CTD holders for stays up to 3 months.",
        "evisa": False,
        "evisa_info": None
    },
}

# Document checklists by purpose
DOCUMENT_CHECKLISTS = {
    "Tourism / Holiday": {
        "always_required": [
            "Valid UK Convention Travel Document (must be valid for at least 6 months beyond your return date)",
            "Proof of accommodation (hotel booking, Airbnb confirmation, or host invitation letter)",
            "Proof of onward/return travel (return flight or bus ticket)",
            "Proof of sufficient funds (bank statement showing last 3 months, minimum £500 equivalent recommended)",
            "Travel insurance certificate covering medical and repatriation",
            "Passport-size photographs (minimum 2, white background)",
        ],
        "sometimes_required": [
            "Visa application form (if destination requires a visa)",
            "Visa fee payment receipt",
            "Employer letter confirming approved leave (if employed)",
        ]
    },
    "Visiting Family / Friends": {
        "always_required": [
            "Valid UK Convention Travel Document",
            "Invitation letter from host (signed, with their name, address, and contact details)",
            "Proof of your relationship to the host (photos, correspondence, etc.)",
            "Proof of return travel",
            "Proof of sufficient funds",
            "Travel insurance certificate",
            "Passport-size photographs (minimum 2)",
        ],
        "sometimes_required": [
            "Host's proof of residence in destination country (utility bill or rental agreement)",
            "Visa application form (if required)",
        ]
    },
    "Voluntary Work / Work Experience": {
        "always_required": [
            "Valid UK Convention Travel Document",
            "Official letter from the organisation confirming voluntary (unpaid) placement — must state role, duration, and that no payment is made",
            "Proof of accommodation during placement",
            "Proof of return travel",
            "Proof of sufficient personal funds (voluntary work must not be your only means of support)",
            "Travel insurance including work-related activity cover",
            "Passport-size photographs (minimum 2)",
        ],
        "sometimes_required": [
            "Evidence that voluntary work does not constitute 'gainful employment' (important for ETS No. 31 countries — unpaid voluntary work is exempt from employment restrictions under Article 1(2))",
            "Visa application form (if required by destination)",
            "Organisation's registration/charity number",
        ],
        "important_note": "Under Article 1(2) of ETS No. 31, unpaid voluntary work does NOT count as 'gainful employment'. Your visa-free rights are fully preserved. If an embassy questions this, reference ETS No. 31 Article 1(2) directly."
    },
    "Paid Work / Internship": {
        "always_required": [
            "Valid UK Convention Travel Document",
            "Employment contract or internship offer letter (confirming paid position, role, and duration)",
            "Work visa / work permit for the destination country (required in ALL countries, including ETS No. 31 signatories)",
            "Proof of accommodation during employment",
            "Travel insurance including employer liability cover",
            "Passport-size photographs (minimum 2)",
        ],
        "sometimes_required": [
            "Employer sponsorship documents / Certificate of Sponsorship",
            "Proof of professional qualifications or university enrolment",
            "Health insurance documentation (required in many EU countries for work visas)",
            "Bank statements showing financial stability",
        ],
        "important_note": "⚠️ CRITICAL: Paid work — including paid internships — is classified as 'gainful employment' under ETS No. 31 Article 1(2). This means the visa-free provisions of ETS No. 31 DO NOT APPLY. Even if your destination has ratified ETS No. 31 (e.g. Romania, France, Germany), you MUST obtain a work visa before starting a paid role. This is a common and costly mistake."
    },
    "Study": {
        "always_required": [
            "Valid UK Convention Travel Document",
            "Official acceptance/enrolment letter from the educational institution",
            "Proof of tuition fee payment or scholarship letter",
            "Proof of accommodation (student halls confirmation or rental agreement)",
            "Proof of sufficient funds for duration of study",
            "Travel insurance for full duration of stay",
            "Passport-size photographs (minimum 2)",
        ],
        "sometimes_required": [
            "Student visa (most countries require this for study, even if tourist entry is visa-free)",
            "Language proficiency certificate (IELTS, TOEFL, etc.)",
            "Academic transcripts",
            "Medical examination certificate (for stays over 6 months in some countries)",
        ]
    },
    "Business / Conference": {
        "always_required": [
            "Valid UK Convention Travel Document",
            "Invitation letter from the company or conference organiser on official letterhead",
            "Proof of return travel",
            "Travel insurance including business activity",
            "Passport-size photographs (minimum 2)",
        ],
        "sometimes_required": [
            "Business visa (check destination requirements)",
            "Company registration documents",
            "Conference registration confirmation",
            "Proof of employment or business ownership",
        ]
    },
}

# General CTD info
CTD_INFO = {
    "full_name": "Convention Travel Document",
    "also_known_as": "Refugee Travel Document, Blue Travel Document",
    "issued_by": "UK Home Office",
    "valid_for": "10 years (adults), 5 years (under 16)",
    "legal_basis": "1951 UN Refugee Convention, Article 28",
    "key_rights": [
        "Right of return to the UK at any time",
        "Visa-free travel to ETS No. 31 signatory states for non-gainful purposes (tourism, visiting family, voluntary work)",
        "Same travel rights as UK passport holders in many treaty countries",
    ],
    "key_limitations": [
        "Cannot be used to travel to your country of origin or the country you claimed asylum from",
        "ETS No. 31 visa-free access does NOT apply to paid work/internships (gainful employment) — a work visa is always required",
        "Some countries do not recognise it as a travel document — always check before booking",
        "Does not confer UK citizenship or the right to a UK passport",
    ]
}

# ── AI Legal Context ─────────────────────────────────────────────────────────
# This structured legal knowledge powers the Agentic AI Adviser.
# The AI uses this as authoritative source material, not general knowledge.

AI_LEGAL_CONTEXT = """
=== SECURE PATH: AUTHORITATIVE LEGAL KNOWLEDGE BASE FOR CTD TRAVEL ===

## 1. WHAT IS A CONVENTION TRAVEL DOCUMENT (CTD)?
- Issued by the UK Home Office to refugees and stateless persons granted protection
- Legal basis: 1951 UN Refugee Convention, Article 28
- Also called: Refugee Travel Document, Blue Travel Document
- Valid: 10 years (adults), 5 years (under 16)
- DOES NOT allow travel to country of origin or country you fled from

## 2. ETS NO. 31 — THE STRASBOURG AGREEMENT (1959)
- Full name: Council of Europe Agreement on the Abolition of Visas for Refugees
- Signatories (20 countries): Austria, Belgium, Denmark, Finland, France, Germany, Greece,
  Iceland, Ireland, Italy, Luxembourg, Netherlands, Norway, Portugal, Romania, Spain, Sweden,
  Switzerland, Turkey, United Kingdom
- General rule: CTD holders can enter ETS 31 countries visa-free for up to 90 days

## 3. CRITICAL EXCEPTION — ETS NO. 31 ARTICLE 1(2): GAINFUL EMPLOYMENT
*** THIS IS THE MOST IMPORTANT NUANCE — DO NOT GET THIS WRONG ***
Article 1(2) states the visa-free rights apply ONLY for "non-gainful purposes".
- "Gainful employment" = any work for which you receive payment/salary/stipend
- PAID INTERNSHIP = gainful employment → work visa REQUIRED, even in ETS 31 countries
- UNPAID voluntary work = NOT gainful employment → visa-free rights preserved
- The distinction: is money changing hands from employer to worker? If YES → visa needed

REAL EXAMPLE: Going to Romania (ETS 31 signatory) for a PAID internship:
- Romania IS an ETS 31 country → normally visa-free
- BUT the internship is PAID → this is gainful employment under Article 1(2)
- RESULT: Visa required. The CTD holder must apply for a Romanian work visa.
- If they go without a visa, they are working illegally, regardless of ETS 31 membership.

DURATION ALSO MATTERS:
- Even for non-gainful purposes, stays OVER 90 days require a long-stay visa
- e.g. a 120-day holiday in France would require a long-stay visa even though France is ETS 31

## 4. COUNTRIES REQUIRING VISAS REGARDLESS OF PURPOSE
- Canada: Temporary Resident Visa required (eVisa available)
- United States: B1/B2 visitor visa required (ESTA does not apply to CTD holders)
- Australia: Visitor Visa subclass 600 required (eVisitor/ETA not available)
- New Zealand: Visitor Visa required
- Japan: Visa required (in-person application at Japanese Embassy, London)
- South Korea: Visa required
- UAE: Visa required (cannot obtain on arrival; eVisa through icp.gov.ae)

## 5. COUNTRIES WITH BILATERAL VISA-FREE ARRANGEMENTS (non-ETS 31)
- Morocco: Visa-free up to 90 days under bilateral arrangement
- Tunisia: Visa-free up to 3 months under bilateral arrangement

## 6. KEY DOCUMENTS ALWAYS NEEDED
- CTD must be valid for at least 6 months beyond return date
- Proof of accommodation at destination
- Proof of return/onward travel
- Proof of sufficient funds
- Travel insurance

## 7. COMMON MISTAKES TO WARN USERS ABOUT
1. Assuming ETS 31 = visa-free for paid work → WRONG (Article 1(2))
2. Trying to use ESTA for US travel → CTD holders are NOT eligible for ESTA
3. Forgetting CTD validity (needs 6+ months beyond return date)
4. Not getting travel insurance that covers work-related activities
5. Embassy misinformation: some embassies incorrectly require visas for ETS 31 travel
   (for non-gainful purposes only) — users should cite ETS No. 31 Article directly
6. Country of origin travel: CTD CANNOT be used to visit country of origin

## 8. STUDY VISAS
Even for ETS 31 countries, study usually requires a student visa regardless of duration,
as formal educational enrollment is typically treated separately from tourist entry.

## 9. HOW TO HANDLE EMBASSY MISINFORMATION (ETS 31 countries, non-gainful visits)
Users should say: "I hold a UK Convention Travel Document under the 1951 Refugee Convention.
Under ETS No. 31 (1959 Strasbourg Agreement), to which [COUNTRY] is a signatory, I am
entitled to visa-free entry for non-gainful purposes up to 90 days. Please review this."
"""

ALL_COUNTRIES = sorted(list(ETS_31_COUNTRIES.keys()) + list(BILATERAL_COUNTRIES.keys()))
PURPOSES = list(DOCUMENT_CHECKLISTS.keys())
