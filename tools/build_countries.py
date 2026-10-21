"""
Secure Path — country dataset builder.

Generates countries.json: one record per country (193 UN members + Kosovo,
Palestine, Taiwan, Holy See) describing entry rules for holders of UK-issued
travel documents (refugee CTD, stateless person's document, certificate of travel).

Run:  pip install country_converter && python tools/build_countries.py

Methodology (also shown in the app's "Data & sources" tab):
  * Every record has a STATUS and a CONFIDENCE level, plus the sources behind it.
  * HIGH   = taken from an official legal/government source.
  * MEDIUM = official legal framework + consistent secondary reporting.
  * LOW    = general rule only, not individually verified for this country.
  * When in doubt the dataset errs towards "visa required / confirm" — a false
    "visa-free" is the costly mistake (denied boarding, refusal of entry).
"""

import json
from pathlib import Path

import country_converter as coco

REVIEWED = "2026-10-21"
OUT = Path(__file__).resolve().parent.parent / "countries.json"

# ── Sources ──────────────────────────────────────────────────────────────────
SRC = {
    "ets_text": {"label": "ETS No. 31 treaty text (Council of Europe)",
                 "url": "https://rm.coe.int/16800656cf", "kind": "official"},
    "ets_chart": {"label": "ETS No. 31 signatures & ratifications",
                  "url": "https://www.coe.int/en/web/conventions/full-list?module=signatures-by-treaty&treatynum=031",
                  "kind": "official"},
    "eu_reg": {"label": "EU Regulation 2018/1806, Art. 6(2)",
               "url": "https://eur-lex.europa.eu/eli/reg/2018/1806/2025-12-30/eng", "kind": "official"},
    "eu_notice": {"label": "EU notice of Member State visa exemptions (2023/C 340)",
                  "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX%3A52023XC0927%2801%29",
                  "kind": "official"},
    "ees": {"label": "EU Entry/Exit System & ETIAS (official EU site)",
            "url": "https://travel-europe.europa.eu/", "kind": "official"},
    "ie": {"label": "Irish Government — refugee visa-free travel suspended",
           "url": "https://www.gov.ie/en/department-of-justice-home-affairs-and-migration/press-releases/visa-free-travel-for-people-with-refugee-status-further-suspended/",
           "kind": "official"},
    "us_vwp": {"label": "US State Dept — Visa Waiver Program",
               "url": "https://travel.state.gov/content/travel/en/us-visas/tourism-visit/visa-waiver-program.html",
               "kind": "official"},
    "brp": {"label": "BRPTravel — UK refugee travel document guide (secondary, Aug 2026)",
            "url": "https://brptravel.co.uk/guides/refugee-travel-document", "kind": "secondary"},
    "embassies": {"label": "Foreign embassies in the UK (GOV.UK)",
                  "url": "https://www.gov.uk/government/publications/foreign-embassies-in-the-uk",
                  "kind": "official"},
}

SCHENGEN = {"AT", "BE", "BG", "HR", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IS", "IT",
            "LV", "LI", "LT", "LU", "MT", "NL", "NO", "PL", "PT", "RO", "SK", "SI", "ES", "SE", "CH"}
EU = {"AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT",
      "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"}

# ETS No. 31 — verified against the Council of Europe chart (via whatconvention.org mirror)
ETS31_PARTIES = {"BE", "CZ", "DK", "FI", "FR", "DE", "HU", "IS", "IE", "IT", "LI", "LU", "MT",
                 "NL", "NO", "PL", "PT", "RO", "SK", "ES", "SE", "CH", "GB"}
ETS31_SUSPENDED = {"FR": "France suspended it in 1986", "GB": "the UK suspended it in 2003",
                   "IE": "Ireland suspended it in July 2022"}

# Schengen states that secondary sources report as accepting UK refugee travel documents
# visa-free (and that the EU Art. 6(2) notice framework allows). Everything else in
# Schengen is "confirm" rather than guessed.
SCHENGEN_REPORTED_VISA_FREE = {"DK", "FI", "DE", "GR", "IS", "IT", "LT", "LU", "MT", "NL",
                               "NO", "PL", "RO", "SI", "CH", "HR"}
SCHENGEN_REPORTED_MAY_REQUIRE = {"FR", "ES", "AT", "BE"}

# Official eVisa / online application portals (only ones we are confident exist).
# NOTE: many eVisa systems are nationality-based and may not accept a travel document.
EVISA = {
    "AU": "https://immi.homeaffairs.gov.au/", "NZ": "https://www.immigration.govt.nz/",
    "CA": "https://www.canada.ca/en/immigration-refugees-citizenship.html",
    "IN": "https://indianvisaonline.gov.in/", "KE": "https://www.etakenya.go.ke/",
    "TR": "https://www.evisa.gov.tr/", "EG": "https://visa2egypt.gov.eg/",
    "ET": "https://www.evisa.gov.et/", "LK": "https://eta.gov.lk/",
    "KH": "https://www.evisa.gov.kh/", "VN": "https://evisa.gov.vn/",
    "AE": "https://icp.gov.ae/", "SA": "https://visa.visitsaudi.com/",
    "OM": "https://evisa.rop.gov.om/", "BH": "https://www.evisa.gov.bh/",
    "RW": "https://irembo.gov.rw/", "UG": "https://visas.immigration.go.ug/",
    "TZ": "https://visa.immigration.go.tz/", "ZM": "https://evisa.zambiaimmigration.gov.zm/",
    "AZ": "https://evisa.gov.az/", "GE": "https://www.evisa.gov.ge/",
    "AM": "https://evisa.mfa.am/", "UZ": "https://e-visa.gov.uz/",
    "LA": "https://laoevisa.gov.la/", "ID": "https://evisa.imigrasi.go.id/",
    "TH": "https://www.thaievisa.go.th/", "MY": "https://malaysiavisa.imi.gov.my/",
    "PK": "https://visa.nadra.gov.pk/", "NG": "https://immigration.gov.ng/",
    "ZW": "https://www.evisa.gov.zw/", "MM": "https://evisa.moip.gov.mm/",
    "KG": "https://www.evisa.e-gov.kg/",
}

# FCDO currently advises against all or some travel to all/part of these (check live advice).
FCDO_WARNING = {"AF", "BY", "BF", "CF", "HT", "IR", "IQ", "IL", "PS", "LB", "LY", "ML", "MM",
                "NE", "KP", "RU", "SO", "SS", "SD", "SY", "UA", "VE", "YE", "CD", "NG", "PK",
                "ET", "CM", "TD", "MZ", "MR"}

REGION_OVERRIDE = {"CY": "Europe", "TR": "Europe", "AM": "Asia", "AZ": "Asia", "GE": "Asia"}
MIDDLE_EAST = {"BH", "IR", "IQ", "IL", "JO", "KW", "LB", "OM", "PS", "QA", "SA", "SY", "AE", "YE",
               "EG"}

NAME_FIX = {
    "Brunei Darussalam": "Brunei", "Congo Republic": "Republic of the Congo",
    "DR Congo": "Democratic Republic of the Congo", "Micronesia, Fed. Sts.": "Micronesia",
    "St. Kitts and Nevis": "Saint Kitts and Nevis", "St. Lucia": "Saint Lucia",
    "St. Vincent and the Grenadines": "Saint Vincent and the Grenadines",
    "Türkiye": "Turkey", "Czechia": "Czech Republic", "Cabo Verde": "Cape Verde",
}

ALIASES = {
    "US": ["usa", "u.s.", "u.s.a", "america", "united states of america", "new york", "florida", "california"],
    "GB": ["uk", "britain", "great britain", "england", "scotland", "wales", "northern ireland"],
    "NL": ["holland", "amsterdam", "the netherlands"], "AE": ["uae", "dubai", "abu dhabi", "emirates"],
    "TR": ["turkiye", "türkiye", "istanbul", "antalya"], "CZ": ["czechia", "prague"],
    "CI": ["ivory coast", "cote d'ivoire", "cote divoire"], "CD": ["drc", "dr congo", "congo kinshasa", "kinshasa"],
    "CG": ["congo brazzaville", "congo-brazzaville"], "KR": ["korea", "seoul"], "KP": ["dprk"],
    "MM": ["burma"], "SZ": ["swaziland"], "CV": ["cabo verde"], "TL": ["east timor", "timor leste"],
    "VA": ["vatican", "vatican city", "holy see"], "PS": ["gaza", "west bank", "palestinian territories"],
    "MK": ["macedonia"], "BA": ["bosnia", "sarajevo"], "LA": ["lao"], "GM": ["the gambia"],
    "SA": ["saudi", "ksa", "mecca", "makkah", "medina", "riyadh", "jeddah"], "FR": ["paris", "nice"],
    "IT": ["rome", "milan", "venice", "sicily", "sardinia"], "ES": ["madrid", "barcelona", "tenerife", "ibiza", "majorca", "mallorca", "canary islands", "malaga"],
    "DE": ["berlin", "munich", "frankfurt"], "PT": ["lisbon", "porto", "algarve", "madeira"],
    "IE": ["dublin", "republic of ireland"], "RO": ["bucharest"], "GR": ["athens", "crete", "rhodes", "santorini"],
    "CA": ["toronto", "vancouver", "montreal"], "AU": ["sydney", "melbourne"], "JP": ["tokyo"],
    "NG": ["lagos", "abuja"], "KE": ["nairobi"], "GH": ["accra"], "EG": ["cairo", "sharm el sheikh", "hurghada"],
    "QA": ["doha"], "ID": ["bali", "jakarta"], "MA": ["marrakech", "marrakesh", "casablanca"],
    "TH": ["bangkok", "phuket"], "IN": ["delhi", "mumbai", "goa"], "CN": ["beijing", "shanghai"],
    "HK": [], "BE": ["brussels"], "AT": ["vienna"], "CH": ["geneva", "zurich"], "PL": ["warsaw", "krakow"],
    "HU": ["budapest"], "DK": ["copenhagen"], "SE": ["stockholm"], "NO": ["oslo"], "FI": ["helsinki"],
    "MV": ["maldive islands"], "ZA": ["cape town", "johannesburg"], "ET": ["addis ababa"],
    "TW": ["taipei"], "MX": ["cancun", "mexico city"], "BR": ["rio", "sao paulo"],
}

DEMONYMS = {
    "AF": ["afghan", "afghani"], "ER": ["eritrean"], "IR": ["iranian", "persian"], "IQ": ["iraqi"],
    "SD": ["sudanese"], "SS": ["south sudanese"], "SY": ["syrian"], "SO": ["somali", "somalian"],
    "ET": ["ethiopian"], "AL": ["albanian"], "PK": ["pakistani"], "VN": ["vietnamese"],
    "NG": ["nigerian"], "CD": ["congolese"], "YE": ["yemeni"], "LY": ["libyan"], "PS": ["palestinian"],
    "CM": ["cameroonian"], "UG": ["ugandan"], "ZW": ["zimbabwean"], "MM": ["burmese", "rohingya"],
    "LK": ["sri lankan", "tamil"], "BD": ["bangladeshi"], "IN": ["indian"], "CN": ["chinese"],
    "RU": ["russian"], "UA": ["ukrainian"], "BY": ["belarusian"], "VE": ["venezuelan"],
    "EG": ["egyptian"], "KW": ["kuwaiti"], "LB": ["lebanese"], "TD": ["chadian"], "GN": ["guinean"],
    "GM": ["gambian"], "GH": ["ghanaian"], "KE": ["kenyan"], "RW": ["rwandan"], "BI": ["burundian"],
    "TR": ["turkish"], "GE": ["georgian"], "NP": ["nepali", "nepalese"], "CO": ["colombian"],
    "SV": ["salvadoran", "salvadorian"], "HN": ["honduran"], "HT": ["haitian"], "CU": ["cuban"],
    "JO": ["jordanian"], "MX": ["mexican"], "BR": ["brazilian"], "SL": ["sierra leonean"],
    "LR": ["liberian"], "CI": ["ivorian"], "ML": ["malian"], "SN": ["senegalese"], "MA": ["moroccan"],
    "DZ": ["algerian"], "TN": ["tunisian"], "SA": ["saudi"], "MY": ["malaysian"], "PH": ["filipino"],
}

EXTRAS = [  # non-UN-member entities people travel to / come from
    {"name": "Kosovo", "iso2": "XK", "iso3": "XKX", "region": "Europe"},
    {"name": "Palestine", "iso2": "PS", "iso3": "PSE", "region": "Middle East"},
    {"name": "Taiwan", "iso2": "TW", "iso3": "TWN", "region": "Asia"},
    {"name": "Holy See (Vatican City)", "iso2": "VA", "iso3": "VAT", "region": "Europe"},
]


def flag(iso2: str) -> str:
    if len(iso2) != 2 or not iso2.isalpha():
        return "🏳️"
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in iso2.upper())


def region_for(iso2, continent):
    if iso2 in REGION_OVERRIDE:
        return REGION_OVERRIDE[iso2]
    if iso2 in MIDDLE_EAST:
        return "Middle East"
    return {"America": "Americas"}.get(continent, continent)


def base_record(name, iso2, iso3, region):
    return {
        "name": name, "iso2": iso2, "iso3": iso3, "flag": flag(iso2), "region": region,
        "schengen": iso2 in SCHENGEN, "eu": iso2 in EU,
        "ets31": ("suspended" if iso2 in ETS31_SUSPENDED else "party") if iso2 in ETS31_PARTIES else "none",
        "ets31_note": ETS31_SUSPENDED.get(iso2),
        "status": "visa_required", "confidence": "low",
        "summary": "", "notes": [], "sources": [],
        "evisa_url": EVISA.get(iso2), "max_stay_days": 90,
        "validity_months": 6, "fcdo_warning": iso2 in FCDO_WARNING,
        "aliases": ALIASES.get(iso2, []), "demonyms": DEMONYMS.get(iso2, []),
        "reviewed": REVIEWED,
    }


def apply_rules(r):
    c = r["iso2"]
    src = lambda *keys: [SRC[k] for k in keys]  # noqa: E731

    if c == "GB":
        r.update(status="issuer", confidence="high",
                 summary="Your travel document was issued here. You have the right to return to the UK.",
                 sources=src("ets_text"))
        return r

    if r["schengen"]:
        r["validity_months"] = 3
        r["notes"] += [
            "Schengen rule: up to 90 days in any 180-day period, counted across ALL Schengen countries together.",
            "Legal basis: the EU lets each Schengen state exempt refugees and stateless people who live in the UK "
            "(Regulation 2018/1806, Art. 6(2)). The 2023 EU notice shows most states do, 'subject to reciprocity "
            "and overall EU–UK relations'.",
            "Your travel document must be valid for at least 3 months after you leave the Schengen area and "
            "issued within the last 10 years.",
            "Expect biometric registration (fingerprints and photo) at the border under the EU Entry/Exit System.",
        ]
        if c in SCHENGEN_REPORTED_VISA_FREE:
            r.update(status="visa_free", confidence="medium",
                     summary="Usually visa-free for short stays (up to 90 days in 180) for UK refugee travel document holders.")
            r["sources"] = src("eu_reg", "eu_notice", "brp", "ees")
        else:
            reason = ("Some sources report this country may now require a visa from UK travel document holders."
                      if c in SCHENGEN_REPORTED_MAY_REQUIRE else
                      "EU rules allow this country to exempt you, but we could not confirm that it does.")
            r.update(status="check", confidence="medium",
                     summary=f"Rules unclear — confirm with the embassy before booking. {reason}")
            r["sources"] = src("eu_reg", "eu_notice", "brp", "embassies")
        if r["ets31"] == "suspended" and c != "GB":
            r["notes"].append(f"This country is a party to ETS No. 31, but {r['ets31_note']}.")
        return r

    # ── Non-Schengen Europe & micro-states ──
    if c == "IE":
        r.update(status="visa_required", confidence="medium",
                 summary="Visa required. Ireland suspended visa-free travel for refugees in July 2022, and "
                         "UK-issued documents were not on its qualifying list.",
                 sources=src("ie", "ets_chart", "embassies"))
        r["notes"] += ["The Common Travel Area gives free movement to British and Irish citizens only — not "
                       "to travel document holders. No passport check on a route does not mean no visa is needed."]
        return r
    if c in {"SM", "VA"}:
        r.update(status="visa_free", confidence="low",
                 summary="Reached through Italy — if you can enter Italy visa-free, you can usually visit.",
                 sources=src("eu_notice", "brp"))
        return r
    if c in {"MC", "AD"}:
        r.update(status="check", confidence="low",
                 summary="Reached through France/Spain, which may require a visa from you — confirm first.",
                 sources=src("brp", "embassies"))
        return r
    if c in {"AL", "XK", "MD"}:
        r.update(status="visa_free", confidence="low",
                 summary="Reported as visa-free for UK refugee travel document holders — confirm before booking.",
                 sources=src("brp", "embassies"))
        return r
    if c == "TT":
        r.update(status="visa_free", confidence="low",
                 summary="Reported as visa-free for UK refugee travel document holders — confirm before booking.",
                 sources=src("brp", "embassies"))
        return r
    if c == "CY":
        r.update(status="check", confidence="low",
                 summary="EU member outside Schengen with its own national visa rules — confirm with the embassy.",
                 sources=src("embassies"))
        return r

    # ── Well-known strict systems ──
    if c == "US":
        r.update(status="visa_required", confidence="high",
                 summary="Visa required. ESTA/the Visa Waiver Program needs a passport from a participating "
                         "country, so travel document holders must apply for a visa (e.g. B1/B2) at the US Embassy.",
                 sources=src("us_vwp", "embassies"))
        r["notes"] += ["A US visa is needed even to change planes in the US.",
                       "Book the embassy interview early — waiting times can be several months."]
        return r
    if c in {"CA", "AU", "NZ"}:
        prog = {"CA": "an eTA", "AU": "an ETA or eVisitor", "NZ": "an NZeTA"}[c]
        r.update(status="evisa", confidence="medium",
                 summary=f"Visa required, with an online application. {prog.capitalize()} is only for passports "
                         f"of eligible countries, so you will usually need a full visitor visa.",
                 sources=src("embassies"))
        if c == "CA":
            r["notes"].append("You may also need a visa to transit through a Canadian airport.")
        return r

    # ── Everyone else: safe general rule ──
    if r["evisa_url"]:
        r.update(status="evisa", confidence="low",
                 summary="Visa required. An official online (eVisa) system exists, but many only accept national "
                         "passports — check it accepts a travel document before paying.",
                 sources=src("embassies"))
    else:
        r.update(status="visa_required", confidence="low",
                 summary="Visa required in advance (general rule). Visa-free and visa-on-arrival schemes are "
                         "usually tied to nationality and often don't accept travel documents.",
                 sources=src("embassies"))
    return r


def main():
    df = coco.CountryConverter().data
    df = df[df["UNmember"] > 0]
    records = []
    for _, row in df.iterrows():
        iso2 = {"^GR$|^EL$": "GR", "^GB$|^UK$": "GB"}.get(row["ISO2"], row["ISO2"])
        name = NAME_FIX.get(row["name_short"], row["name_short"])
        records.append(base_record(name, iso2, row["ISO3"], region_for(iso2, row["continent"])))
    for e in EXTRAS:
        records.append(base_record(e["name"], e["iso2"], e["iso3"], e["region"]))

    records = [apply_rules(r) for r in records]
    for r in records:  # every record carries the embassy list as a last resort source
        if SRC["embassies"] not in r["sources"]:
            r["sources"].append(SRC["embassies"])
    records.sort(key=lambda r: r["name"])

    OUT.write_text(json.dumps({"reviewed": REVIEWED, "sources": SRC, "countries": records},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print(f"Wrote {len(records)} countries → {OUT.name}")
    print(Counter(r["status"] for r in records))
    print(Counter(r["confidence"] for r in records))


if __name__ == "__main__":
    main()
