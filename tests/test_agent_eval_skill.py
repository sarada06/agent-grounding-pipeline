import unittest
from pathlib import Path

from agent import run_with_skill
from skills.data360_agent_eval.run_agent_eval import build_html_report, evaluate_output


class AgentEvalSkillTests(unittest.TestCase):
    def test_evaluate_output_and_html_report(self):
        hits, misses, score = evaluate_output(
            "We saw one open high severity ticket and a follow-up was drafted.",
            ["open high severity ticket", "follow-up"],
        )

        self.assertEqual(hits, ["open high severity ticket", "follow-up"])
        self.assertEqual(misses, [])
        self.assertEqual(score, 1.0)

        html = build_html_report(
            task="Draft a follow-up",
            identifier="Priya Natarajan",
            output="We saw one open high severity ticket and a follow-up was drafted.",
            expected_facts=["open high severity ticket", "follow-up"],
            score=1.0,
            pass_rate=1.0,
        )

        self.assertIn("Agent Evaluation Report", html)
        self.assertIn("PASS", html)
        self.assertIn("100%", html)

    def test_agent_uses_skill_to_evaluate_output(self):
        report_path = Path("eval/test_agent_report.html")
        if report_path.exists():
            report_path.unlink()

        result = run_with_skill("Draft a follow-up", "Priya Natarajan", output_path=str(report_path))

        self.assertIn("skill_result", result)
        self.assertIn("report_path", result["skill_result"])
        self.assertTrue(report_path.exists())


if __name__ == "__main__":
    unittest.main()
