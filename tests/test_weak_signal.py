"""Weak-signal detection: don't show a confident page when nothing really matched."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core import MiniPromptLibrary
from minipromptlib.models import ContextPacket, WorkflowState
from minipromptlib.ranking import is_weak_signal
from minipromptlib.seeds import seed_library


class IsWeakSignalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp_dir.name) / "prompts.json"
        self.library = MiniPromptLibrary(self.storage)
        root = Path(__file__).resolve().parents[1]
        seed_library(self.library, root / "seeds.md")
        self.prompts = self.library.list_prompts(limit=1000)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_off_vocabulary_general_context_is_weak(self) -> None:
        packet = ContextPacket(last_user_message="I want to refactor the payment module safely")

        self.assertTrue(is_weak_signal(packet, self.prompts))

    def test_general_state_with_real_token_overlap_is_not_weak(self) -> None:
        packet = ContextPacket(
            last_user_message="Explain this to me simply, why should I care about this feature"
        )

        self.assertFalse(is_weak_signal(packet, self.prompts))

    def test_non_general_state_is_never_weak(self) -> None:
        packet = ContextPacket(explicit_state=WorkflowState.UNDECIDED)

        self.assertFalse(is_weak_signal(packet, self.prompts))

    def test_empty_context_in_general_state_is_weak(self) -> None:
        packet = ContextPacket()

        self.assertTrue(is_weak_signal(packet, self.prompts))

    def test_empty_library_is_never_weak(self) -> None:
        packet = ContextPacket(last_user_message="anything at all")

        self.assertFalse(is_weak_signal(packet, []))


class ClarifyFallbackCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp_dir.name) / "prompts.json"
        subprocess.run(
            [sys.executable, "-m", "minipromptlib.cli", "--storage", str(self.storage), "seed", "--panel", "seeds.md"],
            cwd=self.root, check=True, text=True, capture_output=True,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _run(self, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "minipromptlib.cli", "--storage", str(self.storage), *args],
            cwd=self.root, check=False, text=True, capture_output=True, input=input_text,
        )

    def test_non_interactive_weak_signal_offers_runnable_options(self) -> None:
        result = self._run("suggest", "--context", "I want to refactor the payment module safely")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No strong signal", result.stdout)
        self.assertIn("--state undecided", result.stdout)
        self.assertIn("--show-anyway", result.stdout)

    def test_show_anyway_bypasses_the_clarify_prompt(self) -> None:
        result = self._run(
            "suggest", "--context", "I want to refactor the payment module safely", "--show-anyway"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("No strong signal", result.stdout)
        self.assertIn("State: general", result.stdout)

    def test_explicit_state_bypasses_the_clarify_prompt(self) -> None:
        result = self._run(
            "suggest", "--context", "I want to refactor the payment module safely", "--state", "checkpoint"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("No strong signal", result.stdout)

    def test_interactive_clarify_prompt_reranks_on_a_letter_choice(self) -> None:
        result = self._run(
            "suggest", "--context", "I want to refactor the payment module safely", "--interactive",
            input_text="r\nq\n",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No strong signal", result.stdout)
        self.assertIn("State: checkpoint", result.stdout)

    def test_interactive_clarify_prompt_x_shows_original_page(self) -> None:
        result = self._run(
            "suggest", "--context", "I want to refactor the payment module safely", "--interactive",
            input_text="x\nq\n",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("State: general", result.stdout)

    def test_healthy_context_never_triggers_clarify(self) -> None:
        result = self._run(
            "suggest", "--context", "Not sure, lets run through scenarios before deciding."
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("No strong signal", result.stdout)


if __name__ == "__main__":
    unittest.main()
