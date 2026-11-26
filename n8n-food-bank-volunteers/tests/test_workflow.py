"""Offline tests for the exported workflow and demo data: no Docker, no n8n, no key, no Opik.

Run from this example's folder:  python3 -m unittest discover -s tests -v
"""

import json
import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
WORKFLOW = json.loads((HERE / "workflow" / "volunteer-screening.json").read_text())
APPLICANTS = json.loads((HERE / "data" / "applicants.json").read_text())
NODES = {n["name"]: n for n in WORKFLOW["nodes"]}


def targets(node_name: str, output_index: int = 0) -> list[str]:
    return [c["node"] for c in WORKFLOW["connections"][node_name]["main"][output_index]]


class WorkflowWiringTests(unittest.TestCase):
    def test_every_connection_points_at_an_existing_node(self):
        for source, conn in WORKFLOW["connections"].items():
            self.assertIn(source, NODES)
            for branch in conn["main"]:
                for edge in branch:
                    self.assertIn(edge["node"], NODES)

    def test_the_if_node_routes_approvals_and_everything_else_apart(self):
        # Each branch is a different span in Opik, which is how you see which way a sign-up went.
        self.assertEqual(targets("Approved?", 0), ["Welcome note"])
        self.assertEqual(targets("Approved?", 1), ["Coordinator follow-up"])
        self.assertEqual(targets("Welcome note"), ["Reply to form"])
        self.assertEqual(targets("Coordinator follow-up"), ["Reply to form"])

    def test_the_webhook_path_matches_the_demo_script(self):
        path = NODES["Sign-up form"]["parameters"]["path"]
        self.assertIn(f"/webhook/{path}", (HERE / "demo.sh").read_text())


class SecretsAndPromptTests(unittest.TestCase):
    def test_the_credential_is_a_placeholder_filled_at_import_time(self):
        cred = NODES["Screen volunteer (gpt-4o-mini)"]["credentials"]["openAiApi"]
        self.assertEqual(cred["id"], "__OPENAI_CREDENTIAL_ID__")
        self.assertNotRegex(json.dumps(WORKFLOW), r"sk-[A-Za-z0-9]")

    def test_the_system_prompt_names_every_role_and_decision(self):
        system = NODES["Screen volunteer (gpt-4o-mini)"]["parameters"]["messages"]["values"][0]["content"]
        for role in ("warehouse_sorting", "delivery_driver", "distribution_desk", "kids_snack_program"):
            self.assertIn(role, system)
        for decision in ("approve", "follow_up", "not_a_fit"):
            self.assertIn(decision, system)

    def test_every_field_the_prompt_reads_is_present_in_each_applicant(self):
        user = NODES["Screen volunteer (gpt-4o-mini)"]["parameters"]["messages"]["values"][1]["content"]
        fields = set(re.findall(r"\$json\.body\.(\w+)", user))
        self.assertTrue(fields)
        for applicant in APPLICANTS:
            self.assertLessEqual(fields, set(applicant), applicant["name"])


if __name__ == "__main__":
    unittest.main()
