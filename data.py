"""
Secure Path — Eligibility & Document Data
Convention Travel Document (CTD) rules based on:
- 1959 Strasbourg Agreement (ETS No. 31)
- Individual country bilateral arrangements
- UK Home Office guidance
"""

# Countries that have ratified ETS No. 31 (Strasbourg Agreement)
# These allow visa-free entry for CTD holders for short stays (typically up to 3 months)
ETS_31_COUNTRIES = {
    "Belgium": {"days": 90, "notes": "Ratified 1960. No visa required for stays up to 90 days."},
    "Denmark": {"days": 90, "notes": "Ratified 1966. No visa required for stays up to 90 days."},
    "France": {"days": 90, "notes": "Ratified 1954. No visa required for stays up to 90 days."},
    "Germany": {"days": 90, "notes": "Ratified 1954. No visa required for stays up to 90 days."},
    "Iceland": {"days": 90, "notes": "Ratified 1955. No visa required for stays up to 90 days."},
    "Ireland": {"days": 90, "notes": "Ratified 1961. No visa required for stays up to 90 days."},
    "Italy": {"days": 90, "notes": "Ratified 1954. No visa required for stays up to 90 days."},
    "Luxembourg": {"days": 90, "notes": "Ratified 1960. No visa required for stays up to 90 days."},
    "Netherlands": {"days": 90, "notes": "Ratified 1956. No visa required for stays up to 90 days."},
    "Norway": {"days": 90, "notes": "Ratified 1955. No visa required for stays up to 90 days."},
    "Portugal": {"days": 90, "notes": "Ratified 1976. No visa required for stays up to 90 days."},
    "Romania": {"days": 90, "notes": "Ratified 1999. No visa required for stays up to 90 days. Note: embassies sometimes incorrectly advise otherwise — your rights are legally protected under ETS No. 31."},
    "Spain": {"days": 90, "notes": "Ratified 1978. No visa required for stays up to 90 days."},
    "Sweden": {"days": 90, "notes": "Ratified 1954. No visa required for stays up to 90 days."},
    "Switzerland": {"days": 90, "notes": "Ratified 1954. No visa required for stays up to 90 days."},
    "United Kingdom": {"days": 90, "notes": "As issuing country — right of return guaranteed."},
    "Austria": {"days": 90, "notes": "Ratified 1974. No visa required for stays up to 90 days."},
    "Finland": {"days": 90, "notes": "Ratified 1990. No visa required for stays up to 90 days."},
    "Greece": {"days": 90, "notes": "Ratified 1960. No visa required for stays up to 90 days."},
    "Turkey": {"days": 90, "notes": "Ratified 1961. No visa required for stays up to 90 days."},
}

# Countries that have separate bilateral agreements or arrangements
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
        "Visa-free travel to ETS No. 31 signatory states",
        "Same travel rights as UK passport holders in many treaty countries",
    ],
    "key_limitations": [
        "Cannot be used to travel to your country of origin or the country you claimed asylum from",
        "Some countries do not recognise it as a travel document — always check before booking",
        "Does not confer UK citizenship or the right to a UK passport",
    ]
}

ALL_COUNTRIES = sorted(list(ETS_31_COUNTRIES.keys()) + list(BILATERAL_COUNTRIES.keys()))
PURPOSES = list(DOCUMENT_CHECKLISTS.keys())
