"""
Activate
--------
A minimal agent that demonstrates the pattern Data 360 sells: an agent
grounding itself in unified data via a tool call, not a hard-coded blob,
before acting on a task.

Grounding always goes through the same functions the MCP server exposes
(mcp_server.get_customer_context / list_at_risk_customers) — so this
script and a real MCP client are grounding against identical logic.

Generation step:
  - If ANTHROPIC_API_KEY is set, calls Claude for a real grounded draft.
  - Otherwise falls back to a deterministic template so the pipeline is
    runnable and demoable with zero setup.
"""

import json
import os
import sys

from mcp_server import get_customer_context, list_at_risk_customers
from skills.data360_agent_eval.run_agent_eval import run_agent_eval


def generate_with_claude(task: str, context: dict) -> str:
    import anthropic
    client = anthropic.Anthropic()
    prompt = (
        f"You are a customer success assistant. Using ONLY the grounding data below, "
        f"complete this task: {task}\n\n"
        f"Grounding data (unified customer record):\n{json.dumps(context, indent=2)}\n\n"
        f"Do not invent any facts not present in the grounding data."
    )
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")


def generate_with_template(task: str, context: dict) -> str:
    """Deterministic fallback — still fully grounded, just not LLM-authored."""
    name = context.get("canonical_name", "the customer")
    company = context.get("company", "their company")
    tickets = context.get("tickets", [])
    open_high = [t for t in tickets if t["status"] == "open" and t["severity"] == "high"]
    risk = context.get("risk_signal", "unknown")

    lines = [f"[TEMPLATE FALLBACK — no ANTHROPIC_API_KEY set]", ""]
    lines.append(f"Task: {task}")
    lines.append(f"Grounded draft for {name} ({company}) — risk signal: {risk}")
    if open_high:
        lines.append(
            f"Priority: {len(open_high)} open high-severity ticket(s), "
            f"including \"{open_high[0]['issue']}\" (opened {open_high[0]['opened_date']})."
        )
    lines.append(
        f"Suggested opening line: \"Hi {name.split()[0]}, I wanted to personally follow up "
        f"on the open item(s) affecting your account — we take this seriously and I want "
        f"to make sure it's resolved quickly.\""
    )
    return "\n".join(lines)


def run_with_skill(task: str, identifier: str, output_path: str | None = None, pass_threshold: float = 0.8):
    print(f"--- ACTIVATE: '{task}' for '{identifier}' ---\n")

    context_json = get_customer_context(identifier)
    context = json.loads(context_json)
    if "error" in context:
        print(context["error"])
        return {"error": context["error"]}

    print("Grounding context retrieved via MCP tool `get_customer_context`:")
    print(context_json)
    print()

    if os.environ.get("ANTHROPIC_API_KEY"):
        output = generate_with_claude(task, context)
    else:
        output = generate_with_template(task, context)

    print("--- AGENT OUTPUT ---")
    print(output)

    skill_result = run_agent_eval(
        task,
        identifier,
        output_path=output_path,
        pass_threshold=pass_threshold,
        agent_output=output,
    )
    print("--- SKILL EVAL ---")
    print(json.dumps({"verdict": skill_result["verdict"], "score": skill_result["score"], "report_path": skill_result["report_path"]}, indent=2))
    return {"output": output, "skill_result": skill_result}


def run(task: str, identifier: str):
    return run_with_skill(task, identifier)


if __name__ == "__main__":
    task_arg = sys.argv[1] if len(sys.argv) > 1 else "Draft a proactive follow-up for an at-risk customer"
    id_arg = sys.argv[2] if len(sys.argv) > 2 else "Priya Natarajan"
    run(task_arg, id_arg)
