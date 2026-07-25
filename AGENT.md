# Data360 Agent Guide

## Purpose
This workspace contains a small prototype for an agent that grounds responses in unified customer data through MCP tools instead of relying on hard-coded context.

## Core workflow
1. Run the data pipeline first if needed:
   ```bash
   .\.venv\Scripts\python.exe harmonize.py
   ```
2. Use the MCP-backed customer context to ground the agent response.
3. For evaluation, run the skill:
   ```bash
   .\.venv\Scripts\python.exe skills/data360_agent_eval/run_agent_eval.py "recommend next steps for Maria" "Maria Gonzales"
   ```
4. Review the generated HTML report in [eval/agent_eval_report.html](eval/agent_eval_report.html).

## Expected behavior
- The agent should answer using only the customer context retrieved from the MCP tool.
- It should avoid unsupported claims and remain grounded in the available data.
- When a customer has open high-severity tickets or high risk, the recommended action should be proactive outreach and issue resolution.

## Files to know
- [agent.py](agent.py) — main agent entry point
- [mcp_server.py](mcp_server.py) — MCP tool implementation
- [harmonize.py](harmonize.py) — data harmonization and risk derivation
- [skills/data360_agent_eval/run_agent_eval.py](skills/data360_agent_eval/run_agent_eval.py) — evaluation skill

## Notes
- The default fallback mode works without an API key.
- If `ANTHROPIC_API_KEY` is set, the agent can use Claude for richer output.
