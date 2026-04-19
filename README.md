# AEO/GEO Research Observatory

A public, longitudinal research dataset tracking which sources AI engines cite when answering questions in three B2B niches: content operations and marketing, B2B SaaS and fintech, and AEO/GEO itself.

Every month, a scheduled pipeline runs a fixed set of 50–60 research queries across three AI engines, normalizes the citation output, commits raw data to a version-controlled SQLite database, and generates a markdown report. The methodology is public, the data is open, and the code is the research instrument.

There is no equivalent publicly available dataset. Existing AEO/GEO research is either proprietary, behind lead-gen walls, or one-shot rather than longitudinal.

**Operator:** Greg Roxburgh — content operations consultant, Seoul

---

## Engine Coverage

| Engine | API | Status |
|---|---|---|
| ChatGPT | OpenAI Responses API with web search | Active (V1) |
| Perplexity | Sonar API | Active (V1) |
| Claude | Anthropic API with web search | Active (V1) |
| Gemini | — | Deferred to V4 (grounding reliability assessment pending) |
| Google AI Mode | — | Excluded (no API available) |

Model versions are recorded for every run. Changes are flagged as a confound in reports, not silently absorbed.

---

## What's in This Repo

| Path | Contents |
|---|---|
| `/prompts/prompts.yaml` | Full query set used in every run, version-controlled |
| `/data/observatory.db` | SQLite database with all raw citation data, committed per run |
| `/reports/` | Monthly markdown reports (auto-generated, human-reviewed before announcement) |
| `/src/` | Pipeline source code |
| `METHODOLOGY.md` | Full research protocol |
| `TECH-SPEC.md` | Technical specification (schema, API contracts, workflow) |

The SQLite database and monthly reports are committed to this repo on purpose. They are the research artifact.

---

## How to Replicate

Requirements: Python 3.12, API keys for OpenAI, Perplexity, and Anthropic.

```bash
git clone https://github.com/<owner>/aeo-geo-research-lab.git
cd aeo-geo-research-lab
cp .env.example .env          # add your API keys to .env
pip install -r requirements.txt
python run.py test             # validates keys, schema, and API connectivity
python run.py run              # runs the full query set
python run.py report           # generates a markdown report from results
```

The Notion review gate (`NOTION_API_KEY`, `NOTION_REVIEW_DATABASE_ID`) is optional for local runs.

Full protocol details: [METHODOLOGY.md](METHODOLOGY.md)
Technical specification: [TECH-SPEC.md](TECH-SPEC.md)

---

## License

MIT — Greg Roxburgh, 2026
