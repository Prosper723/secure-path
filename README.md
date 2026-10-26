# Secure Path

**Clear visa answers for people travelling on UK Home Office travel documents.**

Refugees and stateless people in the UK can't travel on a national passport. They travel on a Convention
Travel Document, a Stateless Person's Travel Document or a Certificate of Travel. Visa rules for these
documents are scattered across embassy websites, EU regulations and international treaties, and they often
contradict each other. Secure Path brings them together in one app: enter a trip and get a clear verdict,
the reasoning behind it, and exactly what to do next.

Final-year GovTech prototype, BSc (Hons) Business Technology, Manchester Metropolitan University (5Z6Z1002).

<!-- Add a screenshot of the "Check a trip" verdict screen here:
![Secure Path – trip check](docs/screenshot-check.png)
-->

## What it does

- **Check a trip:** a rules engine gives a verdict (visa-free, visa required, or confirm before booking) with
  step-by-step reasoning, a document checklist, a trip plan and a ready-to-send letter.
- **Where to apply:** finds the right embassy or consulate for 191 countries, sorted by distance from where
  the user lives.
- **World map:** an interactive view of all 197 countries, coloured by status and confidence level.
- **AI adviser:** answers follow-up questions in plain English. The AI explains the rules engine's verdict but
  can never change it, so answers stay grounded in sourced evidence.
- **Your rights and Data & sources:** every answer links back to its official source, with a confidence level
  and the date it was checked.

## Built with

Python · Streamlit · pandas · Plotly · pytest · Anthropic / OpenAI APIs (optional)

**Highlights**
- Rules engine separated from the AI layer, so the AI can explain answers but cannot invent them
- Data pipeline that builds country and embassy datasets from official FCDO lists and embassy evidence
- Source monitoring that flags official pages for human review when they change
- 35 automated tests covering data integrity, the engine and the adviser
- Privacy by design: diplomats' names are dropped and no API key is stored in the code

## Run it

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

Run the tests with `python -m pytest -q`.

## Live AI (optional)

The adviser works without any key, using the rules engine. To switch on live AI, either:

- paste a key under **Ask the adviser → AI settings**, or
- set an environment variable before starting: `ANTHROPIC_API_KEY` (console.anthropic.com) or
  `OPENAI_API_KEY` (platform.openai.com), or
- add it to `.streamlit/secrets.toml`, e.g. `ANTHROPIC_API_KEY = "sk-ant-..."`.

The AI explains the rules engine's verdict but can never change it.

## How it fits together

| File | Role |
|---|---|
| `countries.json` | 197 countries: status, confidence level, sources, notes (generated) |
| `tools/build_countries.py` | Builds `countries.json` from documented rules, sources and embassy evidence |
| `tools/monitor_sources.py` | Re-fetches official pages and flags changes for human review |
| `missions.json` | 191 countries' embassies, visa sections, consulates and honorary consuls in the UK (generated) |
| `tools/build_missions.py` | Builds `missions.json` from the FCDO lists in `tools/fcdo_lists/` |
| `contacts.py` | Finds the right office for a country, sorted by distance from where the user lives |
| `data.py` | Loads the data, document types, purposes, checklists, AI knowledge base |
| `engine.py` | Rules engine: one `assess(trip)` → verdict + reasoning steps + actions |
| `adviser.py` | Language understanding, conversation memory, demo/live AI replies |
| `ui.py` | Design system (verdict card, step list, timeline, chips) |
| `app.py` | Streamlit app: Check a trip · World map · Adviser · Your rights · Data & sources |
| `tests/` | 35 tests covering data integrity, the engine and the adviser |

## Data and confidence

Every country has a confidence level: **Embassy-verified** (the destination's own embassy states the rule
for UK-issued documents — quote, URL and date stored), **High** (official source), **Medium** (official
framework, not confirmed by the embassy) or **General rule**. A country is only shown as visa-free with
embassy evidence; evidence older than 180 days falls back to "confirm before booking".

Embassy-verified (21 Oct 2026): Germany, Italy, Switzerland — visa-free for blue/red documents;
Belgium, Spain — Schengen visa required.

**Key legal finding:** the UK suspended ETS No. 31 in 2003. Under Art. 7(2), UK-issued documents can't
claim its benefits. For Schengen countries, visa-free travel for UK-resident refugees now depends on EU
Regulation 2018/1806, Art. 6(2).

Guidance only — not legal advice.

## Updating embassy contacts

The FCDO republishes these lists roughly every one to two months. To find out:

1. **Get an email** — on the GOV.UK page (https://www.gov.uk/government/publications/foreign-embassies-in-the-uk)
   click **"Get emails about this page"**. GOV.UK emails you whenever the lists change.
2. **Or check with one command** — `python tools/check_fcdo_updates.py`. It asks GOV.UK's public API what's new,
   shows the change notes, downloads the new files into `tools/fcdo_lists/` (older versions move to `archive/`),
   rebuilds `missions.json` and lists which countries' details changed. Add `--yes` to skip the question, or
   `--check` to only report.
3. **The app warns you** — if the lists are more than 3 months old, the "Where to apply" tab says so.

After updating, run `python -m pytest -q` and spot-check a few countries. GOV.UK sometimes publishes a list
as Word (.docx) instead of .odt; both are supported. Only public office details are kept — diplomats' names are
dropped.

## Going public (GitHub or a hosted demo)

- **No API key is stored in the code.** Without a key the adviser runs in rules-engine mode, which is free and
  needs nothing. A key is only used if you paste one into *AI settings*, set an `ANTHROPIC_API_KEY` /
  `OPENAI_API_KEY` environment variable, or add it to `.streamlit/secrets.toml`.
- `.gitignore` keeps `secrets.toml`, `.env` files and the raw FCDO lists (which name diplomats) out of the repo.
- On a public hosted demo, **don't put your own key in the host's secrets**: every visitor would spend your credit.
  Leave it in rules-engine mode; visitors who want live AI can paste their own key, which lasts only for their session.

## Author

**Chibuzo Prosper Onyiwe** · Business Technology, Manchester Metropolitan University ·
[LinkedIn](https://www.linkedin.com/in/prosper-onyiwe)
