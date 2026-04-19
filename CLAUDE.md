# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

This is a **batch research pipeline** (not a user-facing app) for an AEO/GEO Research Observatory. It runs monthly across three AI engines (ChatGPT, Perplexity, Claude) to study citation patterns, generating longitudinal datasets committed directly to the repo. The repo itself is the research artifact — every commit is part of the public record.

**Status:** V1 Scoping complete. Implementation not yet started. The primary execution path is a GitHub Actions scheduled workflow running on the first of each month.

---

## Source of Truth Documents

Maintain these four files in the repo root:

- `PRD.md` — What we are building. Goals, user stories, features, research integrity principles, definition of done, and the living project plan.
- `TECH-SPEC.md` — How we are building it. Tech stack, data schema, API contracts, folder structure.
- `session-log.md` — What just happened. Running log of changes and next steps.
- `decisions-log.md` — Why we chose X over Y. Capture reasoning in the moment.

AI behavioral rules live in this file only. Do not duplicate them in other docs.

---

## Tech Stack

- **Language:** Python
- **Dependencies:** `openai`, `anthropic`, `requests`, `python-dotenv`, `pyyaml` (pinned in `requirements.txt`)
- **Data persistence:** SQLite at `/data/observatory.db` — committed to repo on purpose, never add to `.gitignore`
- **Orchestration:** GitHub Actions scheduled monthly workflow
- **External APIs:** OpenAI (ChatGPT + web search), Perplexity Sonar, Anthropic (Claude + web search), Notion (review gate)
- **Config:** `prompts.yaml` for query definitions; `.env` for secrets (never committed)

---

## Commands

Once implemented, the expected commands are:

```bash
pip install -r requirements.txt        # install dependencies
python run.py test                     # dry-run single query through all three engines
python run.py run                      # full monthly research run
python run.py report                   # generate markdown report from latest run data
```

For the GitHub Actions workflow, secrets must be set in repo settings: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `PERPLEXITY_API_KEY`, `NOTION_API_KEY`.

---

## Architecture

The pipeline has five logical layers:

1. **Query layer** — `prompts.yaml` defines 50–60 queries across three ICP zones. Five queries run monthly with rewording variants (prompt stability sub-study).
2. **Engine integrations** — One module per engine (ChatGPT, Perplexity, Claude). Each normalizes its response to a common schema before writing to SQLite.
3. **Data layer** — SQLite tables: `runs`, `citations`, `queries`, `costs`. Schema defined in `TECH-SPEC.md`.
4. **Report generation** — Template-based markdown reports written to `/reports/YYYY-MM.md`, auto-generated and committed, human-reviewed via Notion before external announcement.
5. **Budget circuit breaker** — Enforces $40/month API cost cap. Any run that would exceed the cap must halt and alert rather than continue.

Three runs minimum per query per engine per month is a research integrity requirement, not a preference.

---

## Security Perimeter

- Never read or index `.env`, `.env.local`, or any file listed in `.gitignore`.
- Use `.env.example` as the only reference for environment variable names.
- Zero API key exposure in chat, logs, commits, or output. No exceptions.
- This is a public repo. Assume every committed file is world-readable forever.

---

## Research Integrity (Non-Negotiable)

These constraints in PRD.md Section 7 must not be eroded by any code change:

- Three runs minimum per query per engine per month
- Methodology public from day one (auditable, version-controlled)
- Null findings published (no selection bias)
- Scope honesty — all claims frame their boundaries
- Prompt stability sub-study — 5 queries run with rewording variants monthly
- Model version pinning — versions recorded for every run, changes flagged in reports

Any change that reduces transparency is a step backward, even if it makes the code "cleaner."

---

## Execution Workflow (Plan-Before-Code)

For every feature request:

1. **Plan.** Read PRD.md (including the living plan) and TECH-SPEC.md. Produce a step-by-step implementation plan. List files to modify. Flag security risks, budget risks, and logic gaps.
2. **Build.** Implement per the approved plan. One phase at a time — verify it works before starting the next.
3. **Verify.** Re-read changed files. Run relevant scripts or connectivity tests.
4. **Log.** Append outcome to `session-log.md`. Record any new decisions in `decisions-log.md`.

---

## Document Rules

- Update PRD.md and TECH-SPEC.md before writing code for any feature change.
- After every significant change, append to `session-log.md` with what changed and the next step.
- When choosing a library, pattern, or rejecting an alternative, log it in `decisions-log.md`.
- If a decision is already in `decisions-log.md`, do not re-litigate it without flagging the conflict first.

---

## Behavioral Rules

- **Explain before coding.** State what you plan to do and why before writing any code.
- **Keep it modular.** Avoid tight coupling and hardcoded values. Make things configurable through environment variables or config files.
- **Stay in scope.** Do not implement beyond the current plan. Flag improvement ideas and wait for approval.
- **Ask before installing.** If a feature requires a new dependency not in the tech stack, stop and ask. Explain what it is and why you need it.
- **Respect the budget.** Flag any change that could materially increase API cost before implementing it.
- **Reflect at session end.** Suggest improvements to this CLAUDE.md, project performance, prompting, or structure.

---

## Project Health Check

When asked "what is the project health?", produce a status report with four sections:

1. **State Verification.** Identify the last functional change. State whether the most recent `session-log.md` entry matches the most recently modified logic in the files.
2. **Execution Gap.** Name the precise task in progress. Point to the specific file and line number where work stopped.
3. **Blocking Debt.** List all TODO comments and half-finished flags. Rank by impact on the immediate next step.
4. **Assumptions.** State any uncertainties about current build stability or missing dependencies.

Compare the Living Project Plan in PRD.md against the actual codebase and be honest when they have drifted apart.

---

## Error Handling (Build Errors)

- Dependency install fails: check version conflicts before retrying with a different version.
- Linter or type error blocks the build: fix immediately, do not defer.
- Planned approach conflicts with an existing pattern: flag it and propose alignment before proceeding.
- GitHub Actions workflow fails: read the workflow log before making any code change. Do not change secrets or environment variables to "fix" a failing run; find the real cause first.
