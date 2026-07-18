#!/usr/bin/env python3
"""
MiniPromptLib CLI - Quick commands for saving and retrieving mini-prompts
without leaving the terminal or your editor.

Usage examples:
    python -m minipromptlib.cli save "Act as a senior reviewer..." --name "code-review-v2" --tags python review security
    python -m minipromptlib.cli list --tags python
    python -m minipromptlib.cli search "async bug"
    python -m minipromptlib.cli get code-review-v2
    python -m minipromptlib.cli improve prompt_abc123 --instructions "Add more emphasis on type hints and pydantic"
"""

import argparse
import sys
from pathlib import Path

# Allow running as module or directly
try:
    from minipromptlib.core import MiniPromptLibrary
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from core import MiniPromptLibrary


def cmd_save(args):
    lib = MiniPromptLibrary(args.storage)
    pid = lib.save_mini_prompt(
        prompt_text=args.prompt_text,
        name=args.name,
        tags=args.tags,
        category=args.category,
        description=args.description or "",
        overwrite=args.overwrite,
    )
    print(f"✅ Saved prompt: {pid}")
    if args.print:
        entry = lib.get_prompt(pid)
        print("\n--- Prompt Text ---")
        print(entry["prompt_text"])


def cmd_list(args):
    lib = MiniPromptLibrary(args.storage)
    results = lib.list_prompts(
        tags=args.tags,
        category=args.category,
        search=args.search,
        limit=args.limit,
    )
    if not results:
        print("No prompts found matching criteria.")
        return
    print(f"Found {len(results)} prompt(s):\n")
    for e in results:
        tags_str = ", ".join(e.get("tags", []))
        print(f"• {e['id']}  |  {e.get('name', e['id'])}")
        print(f"  Category: {e.get('category')}  |  Tags: [{tags_str}]")
        print(f"  Used: {e.get('usage_count', 0)}×  |  Success rate: {lib._success_rate(e):.0%}")
        if e.get("description"):
            print(f"  Desc: {e['description'][:80]}{'...' if len(e['description'])>80 else ''}")
        print()


def cmd_get(args):
    lib = MiniPromptLibrary(args.storage)
    entry = lib.get_prompt(args.prompt_id)
    if not entry:
        print(f"❌ Prompt '{args.prompt_id}' not found.")
        return
    print(f"ID: {entry['id']}")
    print(f"Name: {entry.get('name')}")
    print(f"Category: {entry.get('category')} | Tags: {', '.join(entry.get('tags', []))}")
    print(f"Version: {entry.get('version', 1)} | Used: {entry.get('usage_count', 0)} times")
    print("\n--- PROMPT TEXT ---\n")
    print(entry["prompt_text"])
    if entry.get("description"):
        print(f"\n[Description: {entry['description']}]")


def cmd_search(args):
    lib = MiniPromptLibrary(args.storage)
    results = lib.keyword_search(args.query, top_k=args.limit)
    if not results:
        print("No matches.")
        return
    print(f"Top matches for '{args.query}':\n")
    for e in results:
        print(f"• {e['id']} ({e.get('name')}) — {e.get('category')}")
        print(f"  {e.get('description', '')[:100]}")
        print()


def cmd_improve(args):
    lib = MiniPromptLibrary(args.storage)
    print("⚠️  improve requires a chat_completion_fn (LLM).")
    print("For now, this CLI prints the current prompt + your instructions.")
    print("Copy the prompt into your favorite SWE AI and ask it to improve with the instructions below.\n")
    entry = lib.get_prompt(args.prompt_id)
    if not entry:
        print(f"❌ Not found: {args.prompt_id}")
        return
    print("=== CURRENT PROMPT ===")
    print(entry["prompt_text"])
    print("\n=== IMPROVEMENT INSTRUCTIONS ===")
    print(args.instructions)
    print("\nTip: Use the Python API with an LLM function for automatic improvement + versioning.")


def cmd_mine(args):
    """Mine a conversation export or pasted text for reusable mini-prompt candidates."""
    lib = MiniPromptLibrary(args.storage)

    # Read conversation
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            conv = f.read()
    elif args.text:
        conv = args.text
    else:
        # Read from stdin
        print("Paste conversation text (Ctrl-D or Ctrl-Z when done):")
        conv = sys.stdin.read()

    if not conv.strip():
        print("No conversation content provided.")
        return

    print("\n🔍 Mining conversation for reusable mini-prompts... (this uses your LLM)\n")

    # For CLI we need a chat fn. We'll use a simple Ollama one if available, else instruct user.
    try:
        from minipromptlib.core import make_ollama_chat_fn
        chat_fn = make_ollama_chat_fn(default_model=args.model)
    except Exception:
        print("⚠️  Could not create Ollama chat function. Please use the Python API directly with your preferred chat_completion_fn for mining.")
        return

    candidates = lib.mine_prompts_from_conversation(
        conv,
        chat_completion_fn=chat_fn,
        model=args.model,
        max_candidates=args.max_candidates,
    )

    if not candidates:
        print("No strong reusable mini-prompt candidates found.")
        return

    print(f"Found {len(candidates)} candidate mini-prompt(s):\n")
    for i, c in enumerate(candidates, 1):
        print(f"{'='*70}")
        print(f"CANDIDATE {i}")
        print(f"Name suggestion: {c['suggested_name']}")
        print(f"Category: {c['suggested_category']} | Tags: {', '.join(c.get('suggested_tags', []))}")
        print(f"Why recommended: {c['why_recommended']}")
        print("\n--- Suggested Prompt Text ---")
        print(c["suggested_prompt_text"])
        print("\n--- Original snippet (for context) ---")
        print(c["original_snippet"][:250] + ("..." if len(c["original_snippet"]) > 250 else ""))
        print()

    print("\nNext steps:")
    print("  • Review the candidates above")
    print("  • Use `python -m minipromptlib.cli save \"<paste prompt>\" --name <name> --tags ...` to save the good ones")
    print("  • Or use the Python API: lib.save_mini_prompt(c['suggested_prompt_text'], name=..., tags=...)")


def main():
    parser = argparse.ArgumentParser(
        prog="minipromptlib",
        description="MiniPromptLib — Save, retrieve, and manage mini-prompts for AI coding agents."
    )
    parser.add_argument("--storage", default="~/.miniprompts/prompts.json", help="Path to prompts.json")

    sub = parser.add_subparsers(dest="command", required=True)

    # save
    p_save = sub.add_parser("save", help="Save a new mini-prompt")
    p_save.add_argument("prompt_text", help="The mini-prompt text (use quotes)")
    p_save.add_argument("--name", "-n", help="Human-friendly name / ID")
    p_save.add_argument("--tags", "-t", nargs="*", default=[], help="Tags e.g. python review async")
    p_save.add_argument("--category", "-c", default="general", help="Category (e.g. review, debug, test, refactor)")
    p_save.add_argument("--description", "-d", default="", help="Short description of what this prompt does")
    p_save.add_argument("--overwrite", action="store_true", help="Overwrite if ID exists")
    p_save.add_argument("--print", action="store_true", help="Print the saved prompt after saving")
    p_save.set_defaults(func=cmd_save)

    # list
    p_list = sub.add_parser("list", help="List prompts (filterable)")
    p_list.add_argument("--tags", "-t", nargs="*", help="Filter by tags (all must match)")
    p_list.add_argument("--category", "-c", help="Filter by category")
    p_list.add_argument("--search", "-s", help="Substring search in name/desc/prompt")
    p_list.add_argument("--limit", "-l", type=int, default=30)
    p_list.set_defaults(func=cmd_list)

    # get
    p_get = sub.add_parser("get", help="Show full text of one prompt")
    p_get.add_argument("prompt_id", help="ID or name of the prompt")
    p_get.set_defaults(func=cmd_get)

    # search
    p_search = sub.add_parser("search", help="Keyword search across prompts")
    p_search.add_argument("query")
    p_search.add_argument("--limit", "-l", type=int, default=8)
    p_search.set_defaults(func=cmd_search)

    # improve (placeholder for now)
    p_improve = sub.add_parser("improve", help="Prepare a prompt for LLM improvement (shows current + instructions)")
    p_improve.add_argument("prompt_id")
    p_improve.add_argument("--instructions", "-i", default="Generalize this prompt and make it more robust. Add edge case and testing guidance.", help="Instructions for the improver LLM")
    p_improve.set_defaults(func=cmd_improve)

    # mine (new)
    p_mine = sub.add_parser("mine", help="Mine prior conversation(s) for reusable mini-prompt patterns to populate the library")
    p_mine.add_argument("--file", "-f", help="Path to conversation export file (txt, md, json)")
    p_mine.add_argument("--text", "-t", help="Raw conversation text (alternative to --file)")
    p_mine.add_argument("--model", "-m", default="qwen2.5-coder:32b", help="Model to use for mining (via Ollama)")
    p_mine.add_argument("--max-candidates", type=int, default=10, help="Maximum number of candidates to extract")
    p_mine.set_defaults(func=cmd_mine)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
