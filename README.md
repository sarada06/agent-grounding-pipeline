# Data 360 Prototype — Ingest → Harmonize → Unify → Activate → Evaluate

A small, runnable analog of Catalogen, built in Salesforce's own Data Cloud
vocabulary, for JR347493 (Data & AI Product Management, Senior Director).

## Why this exists

Talking about Catalogen in an interview is a claim. This is proof — a working
pipeline that touches every verb in Data 360's own pitch, small enough to
walk through live in 5 minutes.

## Pipeline

| Stage | File | What it does |
|---|---|---|
| **Ingest** | `data/*.csv` | Two independently-shaped sources (CRM contacts, support tickets) — deliberately inconsistent naming, the way real systems are. |
| **Harmonize** | `harmonize.py` | Maps both sources onto one common schema. |
| **Unify** | `harmonize.py` | Resolves identity across sources (exact email match, fuzzy-name fallback for typos like "Gonzalez" vs "Gonzales") into `unified_customers.json`. |
| **Activate** | `mcp_server.py` + `agent.py` | Exposes the unified model as MCP tools (`get_customer_context`, `list_at_risk_customers`); an agent calls the tool to ground itself before drafting output — never a hard-coded context blob. |
| **Evaluate** | `eval/` | Golden dataset of 7 query/expected-fact pairs; a fact-presence groundedness score runs with zero setup, and an LLM-as-judge qualitative pass runs automatically if `ANTHROPIC_API_KEY` is set. |

## Run it

```bash
python3 harmonize.py                 # ingest -> harmonize -> unify
python3 agent.py "Draft a follow-up" "Priya Natarajan"   # activate
python3 eval/eval_harness.py         # evaluate
```

No API key required — everything runs with a deterministic template
fallback. Set `ANTHROPIC_API_KEY` to see live Claude-generated, MCP-grounded
output and the LLM-as-judge scoring pass.

To run the actual MCP server for a real client (Claude Code, Claude
Desktop) to connect to: `python3 mcp_server.py`.

## How to talk about it in the interview

- **Identity resolution is the hard part, and it's visible here** — point to
  "Maria Gonzales" (CRM) vs "Maria Gonzalez" (ticket) resolving to one
  record. This is the unglamorous 80% of any unification problem.
- **The MCP layer is the point, not a technicality** — the agent never sees
  a hard-coded blob; it calls a tool, the same pattern a real Data 360 /
  Agentforce agent would use to ground itself in live data.
- **The eval harness is what makes trust operational** — this is the same
  golden-dataset + LLM-as-judge pattern behind the 35% accuracy / 25%
  reliability improvement in the Catalogen work, just small enough to run
  in front of an interviewer.
- **What's intentionally left out**: real Data Cloud's identity resolution,
  streaming ingestion, and consent/governance layers are far more complex
  than this demo's fuzzy-match — worth saying explicitly so it reads as
  informed scoping, not a claim that this *is* Data Cloud.
