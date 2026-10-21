# Secure Path

Clear visa answers for people travelling on UK Home Office travel documents (refugee Convention Travel
Document, Stateless Person's Travel Document, Certificate of Travel). Final-year GovTech prototype,
Manchester Metropolitan University (5Z6Z1002).

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
| `tests/` | 33 tests covering data integrity, the engine and the adviser |

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

GOV.UK republishes the London Diplomatic List, Consulates outside London and Honorary Consuls list
regularly. Download the new `.odt` / `.ods` files into `tools/fcdo_lists/` and run
`python tools/build_missions.py`. Only public office details are kept — diplomats' names are dropped.
