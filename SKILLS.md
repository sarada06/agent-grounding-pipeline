# Data360 Agent Evaluation Skill

## Purpose
This skill runs the Data360 agent against a customer identifier, uses the MCP-backed customer context, evaluates the generated response against expected facts, and writes an HTML report with a PASS/REVIEW verdict.

## Files
- [skills/data360_agent_eval/run_agent_eval.py](skills/data360_agent_eval/run_agent_eval.py) — main skill entry point
- [skills/data360_agent_eval/__init__.py](skills/data360_agent_eval/__init__.py) — package marker
- [eval/agent_eval_report.html](eval/agent_eval_report.html) — generated HTML report

## How to run
From the project root:

```bash
.\.venv\Scripts\python.exe skills/data360_agent_eval/run_agent_eval.py
```

Or provide input directly:

```bash
.\.venv\Scripts\python.exe skills/data360_agent_eval/run_agent_eval.py "recommend next steps for Maria" "Maria Gonzales"
```

## What it does
1. Looks up the selected customer via the MCP tool `get_customer_context`.
2. Runs the agent using either the template fallback or Claude, if available.
3. Evaluates the output for expected facts like follow-up guidance, risk signal, and high-severity ticket context.
4. Writes an HTML report showing the score, hits, misses, and verdict.

## Output
The HTML report is written to:
- [eval/agent_eval_report.html](eval/agent_eval_report.html)

## Notes
- The skill works without an API key using the deterministic template fallback.
- Set `ANTHROPIC_API_KEY` to use Claude-generated responses.
