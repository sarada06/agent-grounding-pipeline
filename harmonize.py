"""
Ingest -> Harmonize -> Unify
-----------------------------
Reads two independently-shaped sources (CRM contacts, support tickets),
reconciles field naming and record identity, and produces one unified
customer model that downstream agents can ground against.

Identity resolution strategy (deliberately simple, documented so it's
easy to explain in an interview):
  1. Exact match on normalized email (primary key — most reliable).
  2. Fallback: normalized name similarity (handles typos like
     "Gonzalez" vs "Gonzales") only when email also roughly matches.
"""

import csv
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
OUT_PATH = Path(__file__).parent / "unified_customers.json"


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z ]", "", name.lower().replace(".", " ")).strip()


def name_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()


def load_crm():
    rows = []
    with open(DATA_DIR / "crm_contacts.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def load_tickets():
    rows = []
    with open(DATA_DIR / "support_tickets.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def harmonize():
    crm_rows = load_crm()
    ticket_rows = load_tickets()

    # INGEST + HARMONIZE: map each source's fields onto a common schema
    contacts_by_email = {}
    for row in crm_rows:
        key = normalize_email(row["email_address"])
        contacts_by_email[key] = {
            "unified_id": row["contact_id"],
            "canonical_name": row["full_name"],
            "canonical_email": row["email_address"],
            "company": row["company"],
            "plan_tier": row["plan_tier"],
            "renewal_date": row["renewal_date"],
            "tickets": [],
        }

    unmatched_tickets = []

    # UNIFY: resolve each ticket to a canonical customer record
    for t in ticket_rows:
        key = normalize_email(t["customer_email"])
        record = contacts_by_email.get(key)

        if record is None:
            # fallback: try name similarity against all known contacts
            best_match, best_score = None, 0.0
            for c in contacts_by_email.values():
                score = name_similarity(t["customer_name"], c["canonical_name"])
                if score > best_score:
                    best_match, best_score = c, score
            if best_match and best_score > 0.75:
                record = best_match
            else:
                unmatched_tickets.append(t)
                continue

        record["tickets"].append({
            "ticket_id": t["ticket_id"],
            "issue": t["issue"],
            "status": t["status"],
            "severity": t["severity"],
            "opened_date": t["opened_date"],
            "source_name_variant": t["customer_name"],  # kept for audit trail
        })

    # Derive a simple risk signal now that data is unified —
    # this is the "activate"-ready layer an agent will query.
    for record in contacts_by_email.values():
        open_high = [tk for tk in record["tickets"] if tk["status"] == "open" and tk["severity"] == "high"]
        open_total = [tk for tk in record["tickets"] if tk["status"] == "open"]
        if open_high:
            risk = "high"
        elif len(open_total) >= 2:
            risk = "medium"
        else:
            risk = "low"
        record["risk_signal"] = risk
        record["open_ticket_count"] = len(open_total)

    unified = list(contacts_by_email.values())

    OUT_PATH.write_text(json.dumps({
        "unified_customers": unified,
        "unmatched_tickets": unmatched_tickets,
    }, indent=2))

    print(f"Unified {len(unified)} customer records from {len(crm_rows)} CRM rows "
          f"+ {len(ticket_rows)} ticket rows.")
    print(f"Unmatched tickets: {len(unmatched_tickets)}")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    harmonize()
