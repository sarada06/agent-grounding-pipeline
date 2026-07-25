import argparse
import html
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp_server import get_customer_context  # noqa: E402


def _get_generators():
    from agent import generate_with_claude, generate_with_template  # noqa: E402
    return generate_with_claude, generate_with_template


def evaluate_output(output: str, expected_facts: list[str]) -> tuple[list[str], list[str], float]:
    hits = [fact for fact in expected_facts if fact.lower() in output.lower()]
    misses = [fact for fact in expected_facts if fact not in hits]
    score = len(hits) / len(expected_facts) if expected_facts else 1.0
    return hits, misses, round(score, 2)


def build_html_report(task: str, identifier: str, output: str, expected_facts: list[str], score: float, pass_rate: float) -> str:
    hits, misses, _ = evaluate_output(output, expected_facts)
    verdict = "PASS" if score >= 0.8 else "REVIEW"
    status_class = "pass" if verdict == "PASS" else "review"
    escaped_output = html.escape(output)
    escaped_hits = "<br>".join(html.escape(h) for h in hits) or "None"
    escaped_misses = "<br>".join(html.escape(m) for m in misses) or "None"
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>Agent Evaluation Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; background: #f7f9fc; color: #101828; }}
    .card {{ background: white; padding: 16px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 16px; }}
    .pass {{ color: #027a48; font-weight: bold; }}
    .review {{ color: #b54708; font-weight: bold; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d7dde5; padding: 8px; text-align: left; }}
    th {{ background: #eef3f8; }}
    pre {{ white-space: pre-wrap; background: #f2f4f7; padding: 12px; border-radius: 8px; }}
  </style>
</head>
<body>
  <h1>Agent Evaluation Report</h1>
  <div class=\"card\">
    <p><strong>Task:</strong> {html.escape(task)}</p>
    <p><strong>Identifier:</strong> {html.escape(identifier)}</p>
    <p><strong>Verdict:</strong> <span class=\"{status_class}\">{verdict}</span></p>
    <p><strong>Pass Rate:</strong> {pass_rate:.0%}</p>
  </div>
  <div class=\"card\">
    <h2>Results</h2>
    <table>
      <tr><th>Metric</th><th>Value</th></tr>
      <tr><td>Fact score</td><td>{score:.2f}</td></tr>
      <tr><td>Hits</td><td>{escaped_hits}</td></tr>
      <tr><td>Misses</td><td>{escaped_misses}</td></tr>
    </table>
  </div>
  <div class=\"card\">
    <h2>Agent Output</h2>
    <pre>{escaped_output}</pre>
  </div>
</body>
</html>
"""


def run_agent_eval(
    task: str,
    identifier: str,
    output_path: str | None = None,
    pass_threshold: float = 0.8,
    agent_output: str | None = None,
    expected_facts: list[str] | None = None,
) -> dict:
    if agent_output is None:
        context_json = get_customer_context(identifier)
        context = json.loads(context_json)

        if "error" in context:
            output = context["error"]
            expected_facts = []
        else:
            generate_with_claude, generate_with_template = _get_generators()
            if os.environ.get("ANTHROPIC_API_KEY"):
                output = generate_with_claude(task, context)
            else:
                output = generate_with_template(task, context)
    else:
        output = agent_output

    if expected_facts is None:
        expected_facts = [
            "open high severity ticket",
            "follow-up",
            "risk signal",
        ]

    hits, misses, score = evaluate_output(output, expected_facts)
    pass_rate = score
    verdict = "PASS" if score >= pass_threshold else "REVIEW"
    report_path = Path(output_path or ROOT / "eval" / "agent_eval_report.html")
    report_path.write_text(build_html_report(task, identifier, output, expected_facts, score, pass_rate), encoding="utf-8")

    return {
        "task": task,
        "identifier": identifier,
        "output": output,
        "expected_facts": expected_facts,
        "hits": hits,
        "misses": misses,
        "score": score,
        "pass_rate": pass_rate,
        "verdict": verdict,
        "report_path": str(report_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the agent evaluation skill and generate an HTML evaluation report")
    parser.add_argument("task", nargs="?", help="Task to give the agent")
    parser.add_argument("identifier", nargs="?", help="Customer identifier to look up")
    parser.add_argument("--output", dest="output", help="Path to the HTML report to write")
    parser.add_argument("--threshold", type=float, default=0.8, help="Pass threshold for the report verdict")
    args = parser.parse_args()

    task = args.task or input("Enter the task for the agent: ").strip() or "Draft a proactive follow-up for an at-risk customer"
    identifier = args.identifier or input("Enter the customer identifier: ").strip() or "Priya Natarajan"

    result = run_agent_eval(task, identifier, output_path=args.output, pass_threshold=args.threshold)
    print(json.dumps(result, indent=2))
    print(f"\nReport written to: {result['report_path']}")


if __name__ == "__main__":
    main()
