"""Fast terminal and JSON surface for the workflow prompt navigator."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .capture import create_capture_draft, save_capture_draft
from .classifier import classify_workflow_state
from .core import MiniPromptLibrary, make_ollama_chat_fn
from .harvest import DUPLICATE_THRESHOLD, HarvestDraft, build_drafts, detect_candidates
from .models import ContextPacket, WorkflowState
from .navigator import InvalidChoiceError, WorkflowNavigator
from .ranking import is_weak_signal, page_ranked_prompts
from .seeds import default_seed_panel, seed_library


def resolve_storage_path(cli_value: str | None) -> str:
    """Resolve the storage path: --storage flag > MINI_STORAGE env var > default."""
    if cli_value:
        return cli_value
    env_value = os.environ.get("MINI_STORAGE")
    if env_value:
        return env_value
    return "~/.miniprompts/prompts.json"


def _library(args: argparse.Namespace) -> MiniPromptLibrary:
    args.storage = resolve_storage_path(getattr(args, "storage", None))
    return MiniPromptLibrary(args.storage)


def _packet(args: argparse.Namespace) -> ContextPacket:
    state = WorkflowState(args.state) if getattr(args, "state", None) else None
    return ContextPacket(
        last_agent_message=getattr(args, "agent_message", "") or "",
        last_user_message=getattr(args, "context", "") or "",
        build_status=getattr(args, "build_status", "") or "",
        explicit_state=state,
    )


def cmd_save(args: argparse.Namespace) -> None:
    library = _library(args)
    prompt_id = library.save_mini_prompt(
        args.prompt_text,
        name=args.name,
        tags=args.tags,
        category=args.category,
        description=args.description,
        overwrite=args.overwrite,
    )
    print(f"Saved prompt: {prompt_id}")


def cmd_list(args: argparse.Namespace) -> None:
    library = _library(args)
    results = library.list_prompts(
        tags=args.tags, category=args.category, search=args.search, limit=args.limit, folder=args.folder
    )
    for prompt in results:
        print(f"{prompt['id']} | {prompt.get('name', prompt['id'])}")
    if not results:
        print("No prompts found matching criteria.")


def cmd_get(args: argparse.Namespace) -> None:
    prompt = _library(args).get_prompt(args.prompt_id)
    if not prompt:
        raise SystemExit(f"Prompt '{args.prompt_id}' not found.")
    print(prompt["prompt_text"])


def cmd_search(args: argparse.Namespace) -> None:
    results = _library(args).keyword_search(args.query, top_k=args.limit)
    for prompt in results:
        print(f"{prompt['id']} | {prompt.get('name', prompt['id'])}")
    if not results:
        print("No matches.")


def cmd_rm(args: argparse.Namespace) -> None:
    library = _library(args)
    entry = library.get_prompt(args.prompt_id)
    if not entry:
        raise SystemExit(f"Prompt '{args.prompt_id}' not found.")
    if not args.yes:
        answer = input(f"Delete '{entry.get('name', entry['id'])}' ({entry['id']})? [y/N]: ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Not deleted.")
            return
    library.delete_prompt(entry["id"])
    print(f"Deleted: {entry['id']}")


def cmd_rename(args: argparse.Namespace) -> None:
    library = _library(args)
    try:
        updated = library.rename_prompt(args.prompt_id, args.new_name, overwrite=args.overwrite)
    except (KeyError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Renamed {updated['id']} to: {updated['name']}")


def cmd_edit(args: argparse.Namespace) -> None:
    library = _library(args)
    if (
        args.text is None
        and args.description is None
        and args.tags is None
        and args.category is None
        and args.folder is None
    ):
        raise SystemExit(
            "Nothing to edit. Supply at least one of --text, --description, --tags, --category, --folder."
        )
    try:
        updated = library.edit_prompt(
            args.prompt_id,
            prompt_text=args.text,
            description=args.description,
            tags=args.tags,
            category=args.category,
            folder=args.folder,
        )
    except (KeyError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Updated: {updated['id']} (version {updated['version']})")


def cmd_improve(args: argparse.Namespace) -> None:
    prompt = _library(args).get_prompt(args.prompt_id)
    if not prompt:
        raise SystemExit(f"Prompt '{args.prompt_id}' not found.")
    print("improve requires a configured chat_completion_fn; use the Python API.")
    print(prompt["prompt_text"])
    print(f"Instructions: {args.instructions}")


def cmd_mine(args: argparse.Namespace) -> None:
    """Preserve the optional legacy conversation-mining CLI surface."""
    if not args.model:
        raise SystemExit(
            "mine requires --model <model-id>. The user chooses the model; "
            "there is no built-in default. Supply the exact local Ollama model id you want to use."
        )
    if args.file:
        conversation = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        conversation = args.text
    else:
        conversation = sys.stdin.read()
    if not conversation.strip():
        raise SystemExit("No conversation content provided.")
    try:
        chat = make_ollama_chat_fn(default_model=args.model)
    except Exception as exc:
        raise SystemExit(
            "Mining requires an optional local Ollama client; use the Python API with another chat_completion_fn."
        ) from exc
    candidates = _library(args).mine_prompts_from_conversation(
        conversation,
        chat_completion_fn=chat,
        model=args.model,
        max_candidates=args.max_candidates,
    )
    print(json.dumps(candidates, ensure_ascii=False, indent=2))


def cmd_folders(args: argparse.Namespace) -> None:
    library = _library(args)
    counts = library.list_folders()
    if args.json:
        print(json.dumps(counts, ensure_ascii=False))
        return
    if not counts:
        print("No saved prompts yet. Run: mini seed")
        return
    for folder, count in counts.items():
        print(f"{folder} ({count})")


def cmd_feedback(args: argparse.Namespace) -> None:
    library = _library(args)
    entry = library.get_prompt(args.prompt_id)
    if not entry:
        raise SystemExit(f"Prompt '{args.prompt_id}' not found.")
    if args.helped and args.not_helped:
        raise SystemExit("Choose only one of --helped or --not-helped.")
    if not args.helped and not args.not_helped:
        raise SystemExit("Supply --helped or --not-helped.")
    success = True if args.helped else False
    library.log_usage(entry["id"], success=success)
    verdict = "helped" if success else "did not help"
    print(f"Recorded: {entry.get('name', entry['id'])} {verdict}.")


def cmd_stats(args: argparse.Namespace) -> None:
    library = _library(args)
    if not library.list_prompts(limit=1):
        print("No saved prompts yet. Run: mini seed")
        return
    all_prompts = library.list_prompts(limit=1000)
    total_selections = sum(p.get("selection_count", 0) for p in all_prompts)
    total_usage = sum(p.get("usage_count", 0) for p in all_prompts)
    print(f"Prompts: {len(all_prompts)} | total selections: {total_selections} | total feedback: {total_usage}")

    underperforming = library.get_underperforming_prompts(
        min_usage=args.min_usage, success_threshold=args.success_threshold
    )
    if not underperforming:
        print("No underperforming prompts at the current thresholds.")
        return
    print(f"\nUnderperforming (below {args.success_threshold:.0%} success, min {args.min_usage} uses):")
    for entry in underperforming:
        total = entry.get("success_count", 0) + entry.get("failure_count", 0)
        rate = entry.get("success_count", 0) / total if total else 0.0
        print(f"  {entry['id']} — {rate:.0%} success ({total} uses). Consider: mini improve {entry['id']}")


def cmd_seed(args: argparse.Namespace) -> None:
    inserted = seed_library(_library(args), args.panel, overwrite=args.overwrite)
    print(f"Seeded {inserted} prompt(s).")


def _suggestion_payload(packet: ContextPacket, navigator: WorkflowNavigator, offset: int) -> tuple[dict, object]:
    session = navigator.start(packet)
    session.offset = max(offset, 0)
    page = navigator.current_page(session)
    state = classify_workflow_state(packet).state.value
    payload = {
        "version": 1,
        "state": state,
        "offset": session.offset,
        "suggestions": [
            {
                "number": index,
                "id": item.prompt_id,
                "name": item.prompt.get("name", item.prompt_id),
                "reason": item.reason,
                "selection_count": item.prompt.get("selection_count", 0),
            }
            for index, item in enumerate(page, 1)
        ],
    }
    return payload, session


def cmd_suggest(args: argparse.Namespace) -> None:
    library = _library(args)
    navigator = WorkflowNavigator(library)
    packet = _packet(args)
    if args.interactive:
        if not library.list_prompts(limit=1):
            print("No saved prompts yet. Run: mini seed")
            return
        _interactive_suggest(navigator, packet)
        return

    if (
        not args.choice
        and not args.state
        and not args.json
        and not args.show_anyway
        and is_weak_signal(packet, library.list_prompts(limit=1000))
    ):
        print(
            "No strong signal. Rerun with one of:\n"
            f'  mini suggest --state undecided --context "{args.context}"   (deciding)\n'
            f'  mini suggest --state checkpoint --context "{args.context}"  (reviewing)\n'
            f'  mini suggest --state completion --context "{args.context}"  (shipping)\n'
            f'  mini suggest --context "{args.context}" --show-anyway  (show suggestions anyway)'
        )
        return

    payload, session = _suggestion_payload(packet, navigator, args.offset)

    if args.choice:
        if args.expect:
            page = navigator.current_page(session)
            index = args.choice - 1
            actual_id = page[index].prompt_id if 0 <= index < len(page) else None
            if actual_id != args.expect:
                raise SystemExit(
                    f"Suggestion {args.choice} is now '{actual_id}', not '{args.expect}'. "
                    "The page changed since you read it; rerun suggest and choose again."
                )
        try:
            selected = navigator.select(session, args.choice)
        except InvalidChoiceError as exc:
            raise SystemExit(str(exc)) from exc
        payload["selected"] = {
            "id": selected.prompt_id,
            "prompt_text": selected.prompt["prompt_text"],
        }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
        return

    print(f"State: {payload['state']}")
    if not payload["suggestions"]:
        if not library.list_prompts(limit=1):
            print("No saved prompts yet. Run: mini seed")
            return
        print("No matching prompts. Try again with more context or add a thought.")
        return
    for item in payload["suggestions"]:
        print(f"{item['number']}. {item['name']} — {item['reason']}")
    if "selected" in payload:
        print(f"\nSelected: {payload['selected']['id']}\n")
        print(payload["selected"]["prompt_text"])
    else:
        context = getattr(args, "context", "") or ""
        print(f'More: mini suggest --context "{context}" --offset {args.offset + 3}')
        print('Capture a thought: mini capture "<your thought>"')


def _ask_feedback_for_session(navigator: WorkflowNavigator, session) -> None:
    """On quit, ask once per selected prompt whether it helped. Skip records nothing."""
    for prompt_id in session.selected_prompt_ids:
        entry = navigator.library.get_prompt(prompt_id)
        if not entry:
            continue
        answer = input(f"Did '{entry.get('name', prompt_id)}' help? [y/n/skip]: ").strip().lower()
        if answer in {"y", "yes"}:
            navigator.library.log_usage(prompt_id, success=True)
        elif answer in {"n", "no"}:
            navigator.library.log_usage(prompt_id, success=False)
        # skip (or anything else) records nothing.


def _interactive_suggest(navigator: WorkflowNavigator, packet: ContextPacket) -> None:
    """Small terminal loop for number, more, retry, nesting, and capture actions."""
    session = navigator.start(packet)
    print(f"Storage: {navigator.library.storage_path}")
    if is_weak_signal(session.packet, navigator.library.list_prompts(limit=1000)):
        answer = input(
            "No strong signal. Is this about [d]eciding, [r]eviewing, [s]hipping, or [x] show anyway? "
        ).strip().lower()
        state_map = {"d": WorkflowState.UNDECIDED, "r": WorkflowState.CHECKPOINT, "s": WorkflowState.COMPLETION}
        if answer in state_map:
            navigator.try_again(session, ContextPacket(explicit_state=state_map[answer]))
        # "x" (or anything else) falls through and shows the original page as-is.
    nudged_this_session = False
    if detect_candidates(packet.last_user_message):
        print("That reads like a reusable rule — press [a] to review it as a capture draft.")
        nudged_this_session = True
    while True:
        page = navigator.current_page(session)
        state = classify_workflow_state(session.packet).state.value
        print(f"State: {state} | Page {session.offset // 3 + 1}")
        for number, item in enumerate(page, 1):
            print(f"{number}. {item.prompt.get('name', item.prompt_id)} — {item.reason}")
        action = input(
            "[1-3] use  [v N] view  [m] more  [n] nest  [p] preview  [c] compose  "
            "[r] retry  [a] add thought  [b] back  [h] help  [q] quit: "
        ).strip().lower()
        if action in {"q", "quit"}:
            _ask_feedback_for_session(navigator, session)
            return
        if action in {"h", "help", "?"}:
            print(
                "1-3 = use that suggestion (records a selection)\n"
                "v N = view suggestion N's full text without selecting it\n"
                "m   = show the next small page (more)\n"
                "n   = add another prompt on top of your current selection (nest)\n"
                "p   = preview the composed text of your selections so far\n"
                "c   = same as preview, shown as the final composed mini-prompt\n"
                "r   = retry with revised context\n"
                "a   = capture a new thought as a reusable prompt draft\n"
                "b   = back out of your most recent selection (undoes its count)\n"
                "q   = quit"
            )
            continue
        if action.startswith("v"):
            rest = action[1:].strip()
            if not rest.isdigit():
                print("Use 'v' followed by a number, e.g. 'v 2'.")
                continue
            try:
                viewed = navigator.view(session, int(rest))
            except InvalidChoiceError as exc:
                print(exc)
                continue
            print(f"Viewing (not selected): {viewed.prompt_id}\n\n{viewed.prompt['prompt_text']}")
            continue
        if action in {"m", "more"}:
            if not navigator.can_more(session):
                print("No more matching prompts. Retry with more context or add a thought.")
                continue
            navigator.more(session)
            continue
        if action in {"n", "nest"}:
            if not session.selected_prompt_ids:
                print("Choose a numbered prompt before adding a nested prompt.")
                continue
            navigator.nested_page(session)
            continue
        if action in {"p", "preview"}:
            preview = navigator.composition_preview(session)
            if not preview:
                print("Choose a numbered prompt before previewing a composition.")
            else:
                print(f"Composition preview:\n\n{preview}")
            continue
        if action in {"c", "compose"}:
            composition = navigator.composition_preview(session)
            if not composition:
                print("Choose a numbered prompt before composing it.")
            else:
                print(f"Composed mini-prompt:\n\n{composition}")
            continue
        if action in {"r", "retry"}:
            context = input("Revised context: ").strip()
            navigator.try_again(session, ContextPacket(last_user_message=context))
            if not nudged_this_session and detect_candidates(context):
                print("That reads like a reusable rule — press [a] to review it as a capture draft.")
                nudged_this_session = True
            continue
        if action in {"b", "back"}:
            if not session.selected_prompt_ids:
                print("No selected prompt to back out of.")
                continue
            removed = session.selected_prompt_ids[-1]
            navigator.back(session)
            print(f"Backed out of: {removed}")
            continue
        if action in {"a", "add"}:
            thought = input("Prompt to capture: ").strip()
            draft = create_capture_draft(thought)
            print(f"Draft: {draft.name}\n{draft.prompt_text}")
            if input("Save this draft? [y/N]: ").strip().lower() in {"y", "yes"}:
                saved = save_capture_draft(navigator.library, draft)
                print(f"Saved: {saved}")
            continue
        if action.isdigit():
            try:
                selected = navigator.select(session, int(action))
            except InvalidChoiceError as exc:
                print(exc)
                continue
            print(f"Selected: {selected.prompt_id}\n\n{selected.prompt['prompt_text']}")
            continue
        print("Use a displayed number, v N, m, n, p, c, r, a, b, h, or q.")


def _draft_payload(draft: HarvestDraft) -> dict:
    return {
        "original_text": draft.original_text,
        "generalized_text": draft.generalized_text,
        "changes": draft.changes,
        "suggested_name": draft.suggested_name,
        "suggested_folder": {
            "folder": draft.suggested_folder.folder,
            "confidence": draft.suggested_folder.confidence,
            "reason": draft.suggested_folder.reason,
        },
        "duplicate": (
            {"id": draft.duplicate.prompt_id, "name": draft.duplicate.name, "overlap": draft.duplicate.overlap}
            if draft.duplicate
            else None
        ),
    }


def _read_harvest_input(args: argparse.Namespace) -> str:
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if args.text:
        return args.text
    return sys.stdin.read()


def cmd_harvest(args: argparse.Namespace) -> None:
    """Detect, generalize, and (with per-candidate consent) save reusable prompts.

    Input is only the supplied --file/--text/stdin content -- no conversation
    history is read. Nothing is written to the library without an explicit
    save choice for that specific candidate.
    """
    conversation = _read_harvest_input(args)
    if not conversation.strip():
        raise SystemExit("No content provided. Use --file, --text, or pipe text on stdin.")

    library = _library(args)
    existing_prompts = library.list_prompts(limit=1000)
    drafts = build_drafts(conversation, existing_prompts)

    if args.json:
        print(json.dumps({"version": 1, "candidates": [_draft_payload(d) for d in drafts]}, ensure_ascii=False))
        return

    if not drafts:
        print("No reusable instruction candidates found in the supplied text.")
        return

    print(f"Found {len(drafts)} reusable instruction candidate(s) in the supplied context:\n")
    saved = 0
    for index, draft in enumerate(drafts, 1):
        print(f"[{index}/{len(drafts)}] Original (yours):")
        print(f"  {draft.original_text}")
        if draft.changes:
            print("Generalized (proposed):")
            print(f"  {draft.generalized_text}")
            print(f"  changes: {'; '.join(draft.changes)}")
        else:
            print("Generalized: (no changes proposed -- text already looks general)")
        print(f"Suggested name:   {draft.suggested_name}")
        print(
            f"Suggested folder: {draft.suggested_folder.folder}  "
            f"(reason: {draft.suggested_folder.reason}; confidence: {draft.suggested_folder.confidence})"
        )
        if draft.duplicate:
            print(
                f"Similar existing: {draft.duplicate.name} ({draft.duplicate.overlap:.0%} overlap) "
                f"-- at/above the {DUPLICATE_THRESHOLD:.0%} dedupe threshold"
            )
        folder = draft.suggested_folder.folder
        text_to_save = draft.generalized_text
        while True:
            prompt = (
                "Save [g]eneralized / [o]riginal / [e]dit / change [f]older / [s]kip"
                + (" / [u]pdate existing / save as [v]ariant" if draft.duplicate else "")
                + ": "
            )
            choice = input(prompt).strip().lower()

            if choice in {"s", "skip"}:
                print("Skipped.\n")
                break

            if choice in {"g", "generalized"}:
                text_to_save = draft.generalized_text
                continue

            if choice in {"o", "original"}:
                text_to_save = draft.original_text
                continue

            if choice in {"e", "edit"}:
                edited = input("Enter the text to save: ").strip()
                if edited:
                    text_to_save = edited
                continue

            if choice in {"f", "folder"}:
                new_folder = input("Folder path (e.g. review/async): ").strip().strip("/")
                if new_folder:
                    folder = new_folder
                continue

            if choice in {"u", "update"} and draft.duplicate:
                library.edit_prompt(draft.duplicate.prompt_id, prompt_text=text_to_save, folder=folder)
                print(f"Updated existing: {draft.duplicate.prompt_id}\n")
                saved += 1
                break

            if choice in {"v", "variant"} and draft.duplicate:
                prompt_id = library.save_mini_prompt(
                    text_to_save, name=draft.suggested_name, folder=folder, category="captured"
                )
                print(f"Saved as variant: {prompt_id}\n")
                saved += 1
                break

            if choice in {"y", "yes", "save"}:
                prompt_id = library.save_mini_prompt(
                    text_to_save, name=draft.suggested_name, folder=folder, category="captured"
                )
                print(f"Saved: {prompt_id}\n")
                saved += 1
                break

            print("Use g, o, e, f, s, y" + (", u, or v" if draft.duplicate else "") + ".")
    print(f"Harvest complete: {saved} saved, {len(drafts) - saved} skipped.")


def cmd_capture(args: argparse.Namespace) -> None:
    library = _library(args)
    draft = create_capture_draft(args.prompt_text)
    payload = {
        "name": draft.name,
        "prompt_text": draft.prompt_text,
        "workflow_states": draft.workflow_states,
        "confirmed": bool(args.confirm),
    }
    if args.confirm:
        payload["id"] = save_capture_draft(library, draft, overwrite=args.overwrite)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"Draft: {draft.name} ({', '.join(draft.workflow_states)})")
        print(draft.prompt_text)
        print("Saved." if args.confirm else "Review this draft; rerun with --confirm to save.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MiniPromptLib workflow prompt navigator.")
    parser.add_argument(
        "--storage",
        default=None,
        help="Prompt store path. Falls back to $MINI_STORAGE, then ~/.miniprompts/prompts.json.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    save = sub.add_parser("save", help="Save a prompt")
    save.add_argument("prompt_text")
    save.add_argument("--name", "-n")
    save.add_argument("--tags", "-t", nargs="*", default=[])
    save.add_argument("--category", "-c", default="general")
    save.add_argument("--description", "-d", default="")
    save.add_argument("--overwrite", action="store_true")
    save.set_defaults(func=cmd_save)

    listing = sub.add_parser("list", help="List prompts")
    listing.add_argument("--tags", "-t", nargs="*")
    listing.add_argument("--category", "-c")
    listing.add_argument("--folder", "-f", help="Match this folder or any folder nested under it.")
    listing.add_argument("--search", "-s")
    listing.add_argument("--limit", "-l", type=int, default=30)
    listing.set_defaults(func=cmd_list)

    folders = sub.add_parser("folders", help="Show folder tree with prompt counts")
    folders.add_argument("--json", action="store_true")
    folders.set_defaults(func=cmd_folders)

    get = sub.add_parser("get", help="Show a prompt")
    get.add_argument("prompt_id")
    get.set_defaults(func=cmd_get)

    rm = sub.add_parser("rm", help="Delete a prompt")
    rm.add_argument("prompt_id")
    rm.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")
    rm.set_defaults(func=cmd_rm)

    rename = sub.add_parser("rename", help="Rename a prompt's display name")
    rename.add_argument("prompt_id")
    rename.add_argument("new_name")
    rename.add_argument("--overwrite", action="store_true", help="Allow reusing an existing display name.")
    rename.set_defaults(func=cmd_rename)

    edit = sub.add_parser("edit", help="Edit a prompt's text, description, tags, or category")
    edit.add_argument("prompt_id")
    edit.add_argument("--text")
    edit.add_argument("--description")
    edit.add_argument("--tags", nargs="*")
    edit.add_argument("--category")
    edit.add_argument("--folder")
    edit.set_defaults(func=cmd_edit)

    search = sub.add_parser("search", help="Keyword search")
    search.add_argument("query")
    search.add_argument("--limit", "-l", type=int, default=8)
    search.set_defaults(func=cmd_search)

    improve = sub.add_parser("improve", help="Show a prompt for API-driven improvement")
    improve.add_argument("prompt_id")
    improve.add_argument("--instructions", "-i", default="Generalize this prompt safely.")
    improve.set_defaults(func=cmd_improve)

    mine = sub.add_parser("mine", help="Optionally mine a conversation with a configured local model")
    mine.add_argument("--file", "-f")
    mine.add_argument("--text", "-t")
    mine.add_argument(
        "--model",
        "-m",
        default=None,
        help="Required. The exact model id to use (no built-in default; the user always chooses).",
    )
    mine.add_argument("--max-candidates", type=int, default=10)
    mine.set_defaults(func=cmd_mine)

    feedback = sub.add_parser("feedback", help="Record whether a used prompt helped")
    feedback.add_argument("prompt_id")
    feedback.add_argument("--helped", action="store_true")
    feedback.add_argument("--not-helped", action="store_true")
    feedback.set_defaults(func=cmd_feedback)

    stats = sub.add_parser("stats", help="Show usage stats and underperforming prompts")
    stats.add_argument("--min-usage", type=int, default=3)
    stats.add_argument("--success-threshold", type=float, default=0.6)
    stats.set_defaults(func=cmd_stats)

    harvest = sub.add_parser(
        "harvest", help="Detect and (with consent) save reusable prompts from supplied text"
    )
    harvest.add_argument("--file", "-f")
    harvest.add_argument("--text", "-t")
    harvest.add_argument("--json", action="store_true", help="Print candidate drafts as JSON; never saves.")
    harvest.set_defaults(func=cmd_harvest)

    seed = sub.add_parser("seed", help="Load the authored seed panel")
    seed.add_argument("--panel", default=str(default_seed_panel()))
    seed.add_argument("--overwrite", action="store_true")
    seed.set_defaults(func=cmd_seed)

    suggest = sub.add_parser("suggest", help="Show up to three workflow-aware suggestions")
    suggest.add_argument("--context", default="")
    suggest.add_argument("--agent-message", default="")
    suggest.add_argument("--build-status", default="")
    suggest.add_argument("--state", choices=[state.value for state in WorkflowState])
    suggest.add_argument("--offset", type=int, default=0)
    suggest.add_argument("--choice", type=int)
    suggest.add_argument(
        "--expect",
        default=None,
        help="Abort --choice if the suggestion at that number is no longer this prompt id.",
    )
    suggest.add_argument("--json", action="store_true")
    suggest.add_argument("--interactive", action="store_true")
    suggest.add_argument(
        "--show-anyway",
        action="store_true",
        help="Skip the weak-signal clarifying prompt and show suggestions even with no strong match.",
    )
    suggest.set_defaults(func=cmd_suggest)

    capture = sub.add_parser("capture", help="Preview or confirm a newly captured prompt")
    capture.add_argument("prompt_text")
    capture.add_argument("--confirm", action="store_true")
    capture.add_argument("--overwrite", action="store_true")
    capture.add_argument("--json", action="store_true")
    capture.set_defaults(func=cmd_capture)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
