import json
from pathlib import Path

base = Path(__file__).resolve().parent
input_path = base / "unified_customers.json"
output_path = base / "results.html"

data = json.loads(input_path.read_text(encoding="utf-8"))
customers = data.get("unified_customers", [])

rows = []
for customer in customers:
    rows.append(
        "<tr>"
        f"<td>{customer['canonical_name']}</td>"
        f"<td>{customer['company']}</td>"
        f"<td class=\"risk-{customer['risk_signal']}\">{customer['risk_signal']}</td>"
        f"<td>{customer['open_ticket_count']}</td>"
        f"<td>{customer['plan_tier']}</td>"
        "</tr>"
    )

sections = []
for customer in customers:
    ticket_items = []
    for ticket in customer.get("tickets", []):
        ticket_items.append(
            f"<li>{ticket['issue']} — {ticket['status']} / {ticket['severity']} (opened {ticket['opened_date']})</li>"
        )
    sections.append(
        "<div class=\"card\">"
        f"<h3>{customer['canonical_name']} ({customer['company']})</h3>"
        f"<p><strong>Email:</strong> {customer['canonical_email']}<br>"
        f"<strong>Renewal:</strong> {customer['renewal_date']}<br>"
        f"<strong>Risk:</strong> <span class=\"risk-{customer['risk_signal']}\">{customer['risk_signal']}</span></p>"
        f"<ul>{''.join(ticket_items)}</ul>"
        "</div>"
    )

html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>Data360 Prototype Results</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; background: #f7f9fc; color: #101828; }}
    h1 {{ color: #123; }}
    .card {{ background: white; padding: 16px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 16px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d7dde5; padding: 8px; text-align: left; }}
    th {{ background: #eef3f8; }}
    .risk-high {{ color: #b42318; font-weight: bold; }}
    .risk-medium {{ color: #b54708; font-weight: bold; }}
    .risk-low {{ color: #027a48; font-weight: bold; }}
  </style>
</head>
<body>
  <h1>Data360 Prototype Results</h1>
  <div class=\"card\">
    <p>Generated from the local harmonized customer pipeline.</p>
    <p><strong>Customers:</strong> {len(customers)}</p>
  </div>
  <div class=\"card\">
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Company</th>
          <th>Risk</th>
          <th>Open Tickets</th>
          <th>Plan</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </div>
  <div class=\"card\">
    <h2>Customer Details</h2>
    {''.join(sections)}
  </div>
</body>
</html>
"""

output_path.write_text(html, encoding="utf-8")
print(f"Wrote {output_path}")
