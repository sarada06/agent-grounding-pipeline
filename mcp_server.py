"""
Unify -> Activate
------------------
Exposes the harmonized customer model over MCP so any agent — this demo's
agent, Claude Code, or a real Data 360 / Agentforce agent — can ground
itself in unified data through a standard tool call instead of a
hard-coded context blob.

Run standalone:  python3 mcp_server.py
Run harmonize.py first to (re)generate unified_customers.json.
"""

import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

DATA_PATH = Path(__file__).parent / "unified_customers.json"
mcp = FastMCP("data360-prototype")


def _load():
    if not DATA_PATH.exists():
        raise FileNotFoundError("Run harmonize.py first to generate unified_customers.json")
    return json.loads(DATA_PATH.read_text())["unified_customers"]


@mcp.tool()
def get_customer_context(identifier: str) -> str:
    """
    Look up a single customer's unified record by name or email.
    Returns canonical profile, plan tier, open tickets, and risk signal —
    the grounding context an agent needs before acting on this customer.
    """
    customers = _load()
    ident = identifier.strip().lower()
    for c in customers:
        if ident in c["canonical_name"].lower() or ident == c["canonical_email"].lower():
            return json.dumps(c, indent=2)
    return json.dumps({"error": f"No unified record found for '{identifier}'"})


@mcp.tool()
def list_at_risk_customers(min_risk: str = "medium") -> str:
    """
    List customers at or above a given risk level ('low', 'medium', 'high'),
    derived from open ticket volume and severity. Useful for an agent
    proactively triaging who needs outreach.
    """
    order = {"low": 0, "medium": 1, "high": 2}
    threshold = order.get(min_risk.lower(), 1)
    customers = _load()
    at_risk = [c for c in customers if order.get(c["risk_signal"], 0) >= threshold]
    summary = [
        {
            "name": c["canonical_name"],
            "company": c["company"],
            "risk_signal": c["risk_signal"],
            "open_ticket_count": c["open_ticket_count"],
        }
        for c in at_risk
    ]
    return json.dumps(summary, indent=2)


if __name__ == "__main__":
    mcp.run()
