"""
Evaluate
--------
Runs the agent against a golden dataset and scores groundedness:
did the output actually contain the facts the unified data supports,
or did it drift/hallucinate?

Two scoring modes:
  - Fact-presence check (always runs, zero dependencies): does each
    expected fact appear in the output? This is the CI-friendly,
    deterministic layer.
  - LLM-as-judge (runs only if ANTHROPIC_API_KEY is set): asks Claude
    to rate groundedness 1-5 with a reason, for a qualitative signal
    the fact-presence check can't catch (e.g. subtly wrong tone,
    unsupported inference).
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent import generate_with_template, generate_with_claude  # noqa: E402
from mcp_server import get_customer_context  # noqa: E402

GOLDEN_PATH = Path(__file__).parent / "golden_dataset.json"


def run_case(case: dict) -> dict:
    context_json = get_customer_context(case["identifier"])
    context = json.loads(context_json)

    if "error" in context:
        output = context["error"]
    elif os.environ.get("ANTHROPIC_API_KEY"):
        output = generate_with_claude(case["task"], context)
    else:
        output = generate_with_template(case["task"], context)

    hits = [f for f in case["expected_facts"] if f.lower() in output.lower()]
    misses = [f for f in case["expected_facts"] if f not in hits]
    score = len(hits) / len(case["expected_facts"]) if case["expected_facts"] else 1.0

    return {
        "id": case["id"],
        "identifier": case["identifier"],
        "score": round(score, 2),
        "hits": hits,
        "misses": misses,
        "output": output,
    }


def llm_judge(case: dict, output: str) -> dict:
    """Optional qualitative pass — only runs with a live API key."""
    import anthropic
    client = anthropic.Anthropic()
    prompt = (
        f"Rate how well this agent output is grounded in the task and expected facts. "
        f"Score 1-5 (5 = fully grounded, no unsupported claims). Reply as JSON: "
        f'{{"score": <int>, "reason": "<one sentence>"}}.\n\n'
        f"Task: {case['task']}\nExpected facts present: {case['expected_facts']}\n"
        f"Agent output: {output}"
    )
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"score": None, "reason": text}


def main():
    cases = json.loads(GOLDEN_PATH.read_text())
    results = [run_case(c) for c in cases]

    use_judge = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if use_judge:
        for c, r in zip(cases, results):
            r["llm_judge"] = llm_judge(c, r["output"])

    avg_fact_score = sum(r["score"] for r in results) / len(results)

    print(f"\n{'='*60}")
    print(f"EVAL RUN — {len(results)} cases")
    print(f"{'='*60}")
    for r in results:
        flag = "PASS" if r["score"] == 1.0 else "REVIEW"
        print(f"[{flag}] {r['id']} ({r['identifier']}) — fact score {r['score']}")
        if r["misses"]:
            print(f"         missed facts: {r['misses']}")
        if use_judge and r.get("llm_judge"):
            print(f"         LLM-judge: {r['llm_judge']}")
    print(f"{'='*60}")
    print(f"Average groundedness (fact-presence): {avg_fact_score:.0%}")
    if not use_judge:
        print("(Set ANTHROPIC_API_KEY to also run the LLM-as-judge qualitative pass.)")

    Path("eval_report.json").write_text(json.dumps(results, indent=2))
    print("Full report written to eval/eval_report.json")


if __name__ == "__main__":
    main()
