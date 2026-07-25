# Data 360 Prototype — Ingest → Harmonize → Unify → Activate → Evaluate

A small, runnable analog of Catalogen, built in Salesforce's own Data Cloud

## Why this exists

This is a working
pipeline that showcases how the ingestion to activation works with evals in place

## Pipeline

| Stage | File | What it does |
|---|---|---|
| **Ingest** | `data/*.csv` | Two independently-shaped sources (CRM contacts, support tickets) — deliberately inconsistent naming, the way real systems are. |
| **Harmonize** | `harmonize.py` | Maps both sources onto one common schema. |
| **Unify** | `harmonize.py` | Resolves identity across sources (exact email match, fuzzy-name fallback for typos like "Gonzalez" vs "Gonzales") into `unified_customers.json`. |
| **Activate** | `mcp_server.py` + `agent.py` | Exposes the unified model as MCP tools (`get_customer_context`, `list_at_risk_customers`); an agent calls the tool to ground itself before drafting output — never a hard-coded context blob. |
| **Evaluate** | `eval/` + `skills/data360_agent_eval/` | The agent can now invoke an evaluation skill after generating an answer, score the output against expected facts, and write an HTML report with a PASS/REVIEW verdict. |

## Run it

```bash
.\.venv\Scripts\python.exe harmonize.py                 # ingest -> harmonize -> unify
.\.venv\Scripts\python.exe agent.py "Draft a follow-up" "Priya Natarajan"   # activate + evaluate
.\.venv\Scripts\python.exe skills/data360_agent_eval/run_agent_eval.py "recommend next steps for Maria" "Maria Gonzales"   # run the skill directly
.\.venv\Scripts\python.exe eval/eval_harness.py         # evaluate the golden dataset
```

No API key required — everything runs with a deterministic template
fallback. Set `ANTHROPIC_API_KEY` to see live Claude-generated, MCP-grounded
output and the LLM-as-judge scoring pass.

To run the actual MCP server for a real client (Claude Code, Claude
Desktop) to connect to: `python3 mcp_server.py`.

## Output artifacts

- `unified_customers.json` — the harmonized and unified customer model.
- `eval/agent_eval_report.html` — HTML report produced by the agent evaluation skill.
- `eval/eval_report.json` — structured evaluation results from the golden dataset harness.

## How to understand this more

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
