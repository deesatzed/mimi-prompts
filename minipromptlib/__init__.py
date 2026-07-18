"""MiniPromptLib public package API."""

__all__ = [
    "MiniPromptLibrary",
    "make_ollama_chat_fn",
    "make_openai_compatible_chat_fn",
]


def __getattr__(name: str):
    if name in __all__:
        from .core import (
            MiniPromptLibrary,
            make_ollama_chat_fn,
            make_openai_compatible_chat_fn,
        )

        return {
            "MiniPromptLibrary": MiniPromptLibrary,
            "make_ollama_chat_fn": make_ollama_chat_fn,
            "make_openai_compatible_chat_fn": make_openai_compatible_chat_fn,
        }[name]
    raise AttributeError(name)
