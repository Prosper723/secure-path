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
| `tools/build_countries.py` | Builds `countries.json` from documented rules and sources |
| `data.py` | Loads the data, document types, purposes, checklists, AI knowledge base |
| `engine.py` | Rules engine: one `assess(trip)` → verdict + reasoning steps + actions |
| `adviser.py` | Language understanding, conversation memory, demo/live AI replies |
| `ui.py` | Design system (verdict card, step list, timeline, chips) |
| `app.py` | Streamlit app: Check a trip · World map · Adviser · Your rights · Data & sources |
| `tests/` | 23 tests covering data integrity, the engine and the adviser |

## Data and confidence

Every country has a confidence level: **High** (official source), **Medium** (official framework plus
consistent secondary reporting) or **General rule** (not individually verified). When a rule can't be
confirmed, the app says "visa required" or "confirm before booking", never "visa-free".

**Key legal finding:** the UK suspended ETS No. 31 in 2003. Under Art. 7(2), UK-issued documents can't
claim its benefits. For Schengen countries, visa-free travel for UK-resident refugees now depends on EU
Regulation 2018/1806, Art. 6(2).

Guidance only — not legal advice.
