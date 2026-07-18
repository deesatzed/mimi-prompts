"""
MiniPromptLib
Reusable mini-prompt management for AI coding agents.

Quick start:
    from minipromptlib import MiniPromptLibrary
    lib = MiniPromptLibrary()
    lib.save_mini_prompt("You are a senior Python expert. ...", name="python-senior-review", tags=["python", "review"])
    relevant = lib.select_best_for_context("Fix this async bug...", chat_completion_fn=my_llm_fn)
"""

from .core import MiniPromptLibrary, make_ollama_chat_fn, make_openai_compatible_chat_fn

__all__ = [
    "MiniPromptLibrary",
    "make_ollama_chat_fn",
    "make_openai_compatible_chat_fn",
]
