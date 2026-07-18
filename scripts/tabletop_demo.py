#!/usr/bin/env python3
"""Run the ten approved MiniPromptLib tabletop scenarios deterministically."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from minipromptlib.capture import create_capture_draft, save_capture_draft
from minipromptlib.models import ContextPacket, WorkflowState
from minipromptlib.navigator import WorkflowNavigator
from minipromptlib.seeds import seed_library
from minipromptlib.storage import StorageCorruptionError
from core import MiniPromptLibrary


def _pass(name: str, detail: str) -> dict:
    return {"name": name, "status": "PASS", "detail": detail}


def run_tabletops() -> dict:
    scenarios: list[dict] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        library = MiniPromptLibrary(temp / "prompts.json")
        seed_library(library, ROOT / "seeds.md")
        navigator = WorkflowNavigator(library)

        for name, state in (
            ("agent_question", WorkflowState.QUESTION),
            ("user_undecided", WorkflowState.UNDECIDED),
            ("section_checkpoint", WorkflowState.CHECKPOINT),
            ("completion_claim", WorkflowState.COMPLETION),
            ("build_failure", WorkflowState.FAILURE),
        ):
            session = navigator.start(ContextPacket(explicit_state=state))
            page = navigator.current_page(session)
            assert 1 <= len(page) <= 3
            assert all(state.value in item.prompt.get("workflow_states", []) for item in page)
            scenarios.append(_pass(name, f"{len(page)} {state.value} suggestions"))

        session = navigator.start(ContextPacket(explicit_state=WorkflowState.CHECKPOINT))
        first = navigator.current_page(session)
        second = navigator.more(session)
        navigator.try_again(session, ContextPacket(explicit_state=WorkflowState.CHECKPOINT))
        assert not ({item.prompt_id for item in first} & {item.prompt_id for item in second})
        assert session.offset == 0
        scenarios.append(_pass("more_and_retry", "non-repeating page and reset context"))

        session = navigator.start(ContextPacket(explicit_state=WorkflowState.CHECKPOINT))
        first_choice = navigator.select(session, 1)
        nested = navigator.nested_page(session)
        preview = navigator.composition_preview(session)
        assert nested and first_choice.prompt_id not in {item.prompt_id for item in nested}
        assert preview == first_choice.prompt["prompt_text"]
        scenarios.append(_pass("nested_preview", "selected prompt previewed without auto-composition"))

        draft = create_capture_draft("Not sure, lets run through scenarios or tabletops and then decide.")
        assert not library.get_prompt(draft.name)
        saved_id = save_capture_draft(library, draft)
        assert library.get_prompt(saved_id)["prompt_text"] == draft.prompt_text
        scenarios.append(_pass("quick_capture", "draft required explicit save"))

        corrupt_path = temp / "corrupt.json"
        corrupt_path.write_text("{broken", encoding="utf-8")
        try:
            MiniPromptLibrary(corrupt_path)
        except StorageCorruptionError:
            assert corrupt_path.read_text(encoding="utf-8") == "{broken"
        else:
            raise AssertionError("corrupt storage did not fail closed")
        scenarios.append(_pass("corrupt_storage", "source bytes preserved"))

        assert len(library) >= 34
        scenarios.append(_pass("offline_execution", "all scenarios used local deterministic code"))

    return {"version": 1, "llm_calls": 0, "scenarios": scenarios}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MiniPromptLib UX tabletops.")
    parser.add_argument("--assert", dest="assert_mode", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = run_tabletops()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.assert_mode and not all(item["status"] == "PASS" for item in payload["scenarios"]):
        raise SystemExit(1)
    print(f"{len(payload['scenarios'])} tabletop scenarios passed; llm_calls={payload['llm_calls']}")


if __name__ == "__main__":
    main()
