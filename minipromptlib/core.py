"""Compatibility export for the original MiniPromptLib core API.

The package owns new workflow-navigation modules while this module preserves the
existing public library class during the incremental migration.
"""

from core import (
    MiniPromptLibrary,
    make_ollama_chat_fn,
    make_openai_compatible_chat_fn,
)

__all__ = [
    "MiniPromptLibrary",
    "make_ollama_chat_fn",
    "make_openai_compatible_chat_fn",
]
