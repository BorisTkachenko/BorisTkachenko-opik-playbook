"""Offline tests: no Langflow, no OpenAI key, nothing sent to Opik.

Run from this example's folder:  python3 -m unittest discover -s tests -v
"""

import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def load(name: str):
    # Loaded by path: a module called "setup" would otherwise be confused with setuptools.
    spec = importlib.util.spec_from_file_location(f"gym_{name}", HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PromptTests(unittest.TestCase):
    def setUp(self):
        self.prompt = load("setup").build_prompt()

    def test_only_the_two_langflow_variables_are_templated(self):
        # Langflow turns every {name} into an input field; stray braces would add bogus inputs.
        self.assertEqual(self.prompt.count("{"), 2)
        self.assertIn("{context}", self.prompt)
        self.assertIn("{user_message}", self.prompt)

    def test_the_facts_are_in_the_prompt(self):
        self.assertIn("Plus: 49 dollars per month", self.prompt)
        self.assertIn("Saturday 9:00 Family Swim", self.prompt)

    def test_the_prompt_tells_the_model_to_stay_inside_the_facts(self):
        self.assertIn("ONLY the facts below", self.prompt)


class DemoTests(unittest.TestCase):
    def test_answer_text_reads_the_chat_output_of_a_run_response(self):
        response = {"outputs": [{"outputs": [{"results": {"message": {"text": "We open at 8:00 on Sunday."}}}]}]}
        self.assertEqual(load("demo").answer_text(response), "We open at 8:00 on Sunday.")

    def test_every_conversation_has_its_own_session_and_some_turns(self):
        # One session_id per conversation is what becomes one Opik thread.
        conversations = json.loads((HERE / "data" / "conversations.json").read_text())
        sessions = [c["session_id"] for c in conversations]
        self.assertEqual(len(sessions), len(set(sessions)))
        self.assertTrue(all(c["turns"] for c in conversations))


class TracerPatchTests(unittest.TestCase):
    def test_patch_targets_the_single_line_it_was_written_for(self):
        patch = (HERE / "patch_opik_tracer.py").read_text()
        self.assertIn('ORIGINAL = "self._client.span(**span.__dict__)"', patch)
        self.assertIn("signature(self._client.span).parameters", patch)


if __name__ == "__main__":
    unittest.main()
