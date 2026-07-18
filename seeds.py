#!/usr/bin/env python3
"""Load the complete user-authored MiniPromptLib seed panel."""

from __future__ import annotations

import argparse
from pathlib import Path

from minipromptlib.core import MiniPromptLibrary
from minipromptlib.seeds import seed_library


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed MiniPromptLib from seeds.md.")
    parser.add_argument("--storage", default="~/.miniprompts/prompts.json")
    parser.add_argument("--panel", default=str(Path(__file__).with_name("seeds.md")))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    library = MiniPromptLibrary(args.storage)
    inserted = seed_library(library, args.panel, overwrite=args.overwrite)
    print(f"Seeded {inserted} prompt(s).")
    print(f"Library now has {len(library)} prompt(s) at {library.storage_path}")


if __name__ == "__main__":
    main()
