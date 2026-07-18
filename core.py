#!/usr/bin/env python3
"""
MiniPromptLib - A reusable, self-improving mini-prompt management library
for SWE AI agents (Grok Build, Claude Code, local Codex/Ollama setups, CAM-PULSE, etc.)

Core philosophy:
- Mini-prompts are valuable, versionable assets — not throwaway text.
- The library + the underlying LLM can collaboratively curate, improve, and select them.
- Works locally with zero or minimal dependencies.
- Designed to be imported as a tool/skill in any agentic coding workflow.

Author: Designed for Wayne Satz (O2Satz) — portable across his AI build environments.
"""

from __future__ import annotations
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from minipromptlib.storage import load_prompts, save_prompts


class MiniPromptLibrary:
    """
    Persistent library of mini-prompts with save, retrieve, search, improve, and contextual selection.

    Storage: Single JSON file (easy to git, backup, manually edit).
    Self-improvement data: usage_count, last_used, success_feedback.
    """

    def __init__(self, storage_path: str | Path = "~/.miniprompts/prompts.json"):
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.prompts: Dict[str, Dict[str, Any]] = {}
        self._load()

    # --------------------------- Persistence ---------------------------

    def _load(self) -> None:
        self.prompts = load_prompts(self.storage_path)

    def _save(self) -> None:
        save_prompts(self.storage_path, self.prompts)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # --------------------------- Core CRUD ---------------------------

    def save_mini_prompt(
        self,
        prompt_text: str,
        name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: str = "general",
        description: str = "",
        overwrite: bool = False,
    ) -> str:
        """
        Save a new mini-prompt or update existing one.

        Returns the prompt_id (slug or generated).
        """
        if not prompt_text or not prompt_text.strip():
            raise ValueError("prompt_text cannot be empty")

        prompt_id = self._normalize_name(name) if name else self._generate_id(prompt_text)

        if prompt_id in self.prompts and not overwrite:
            # Auto-version if exists
            existing = self.prompts[prompt_id]
            prompt_id = f"{prompt_id}_v{existing.get('version', 1) + 1}"

        now = self._now()
        entry = {
            "id": prompt_id,
            "name": name or prompt_id,
            "prompt_text": prompt_text.strip(),
            "description": description.strip(),
            "tags": sorted(set(tags or [])),
            "category": category.lower().strip(),
            "created_at": now,
            "last_used": None,
            "usage_count": 0,
            "selection_count": 0,
            "last_selected": None,
            "success_count": 0,
            "failure_count": 0,
            "notes": [],
            "version": 1,
        }

        if prompt_id in self.prompts:
            # Preserve history stats on overwrite/version bump
            old = self.prompts[prompt_id]
            entry["usage_count"] = old.get("usage_count", 0)
            entry["selection_count"] = old.get("selection_count", 0)
            entry["last_selected"] = old.get("last_selected")
            entry["success_count"] = old.get("success_count", 0)
            entry["failure_count"] = old.get("failure_count", 0)
            entry["last_used"] = old.get("last_used")
            entry["notes"] = old.get("notes", [])
            entry["version"] = old.get("version", 1) + 1
            entry["created_at"] = old.get("created_at", now)

        self.prompts[prompt_id] = entry
        self._save()
        return prompt_id

    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full prompt entry by ID or name."""
        pid = self._normalize_name(prompt_id)
        if pid in self.prompts:
            return self.prompts[pid].copy()
        # Try fuzzy match on name
        for pid, entry in self.prompts.items():
            if entry.get("name", "").lower() == prompt_id.lower():
                return entry.copy()
        return None

    def list_prompts(
        self,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List prompts with optional filtering.
        `search` does simple substring match on name/description/prompt_text.
        """
        results = []
        tag_set = set(t.lower() for t in (tags or []))
        cat = category.lower().strip() if category else None
        search_lower = search.lower().strip() if search else None

        for pid, entry in self.prompts.items():
            if cat and entry.get("category") != cat:
                continue
            if tag_set and not tag_set.issubset(set(t.lower() for t in entry.get("tags", []))):
                continue
            if search_lower:
                haystack = " ".join([
                    entry.get("name", ""),
                    entry.get("description", ""),
                    entry.get("prompt_text", ""),
                ]).lower()
                if search_lower not in haystack:
                    continue
            results.append(entry.copy())

        # Sort by usage (most used first) then recency
        results.sort(
            key=lambda e: (
                -e.get("usage_count", 0),
                e.get("last_used") or "1970-01-01",
            ),
            reverse=True,
        )
        return results[:limit]

    # --------------------------- Search & Selection (Requirement 2 & 4) ---------------------------

    def keyword_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Very fast keyword-based relevance for initial candidate filtering."""
        if not query:
            return self.list_prompts(limit=top_k)
        q_words = set(re.findall(r"\w+", query.lower()))
        scored = []
        for pid, entry in self.prompts.items():
            text = " ".join([
                entry.get("name", ""),
                entry.get("description", ""),
                entry.get("prompt_text", ""),
                " ".join(entry.get("tags", [])),
            ]).lower()
            words = set(re.findall(r"\w+", text))
            overlap = len(q_words & words)
            if overlap > 0:
                scored.append((overlap, entry))
        scored.sort(key=lambda x: -x[0])
        return [e.copy() for _, e in scored[:top_k]]

    def select_best_for_context(
        self,
        task_description: str,
        context: str = "",
        top_k: int = 5,
        chat_completion_fn: Optional[Callable] = None,
        model: str = "default",
    ) -> List[Dict[str, Any]]:
        """
        Requirement #4: Intelligently choose the best mini-prompt(s) for the current situation.

        Strategy:
        1. Keyword filter to get a manageable candidate set (cheap).
        2. If chat_completion_fn provided → LLM reranks them with reasoning (smart).
        3. Otherwise → return keyword-ranked list.

        Returns list of best matching prompt entries (with added 'relevance_reason' if LLM used).
        """
        candidates = self.keyword_search(task_description, top_k=max(top_k * 2, 8))

        if not candidates or not chat_completion_fn:
            return candidates[:top_k]

        # Build prompt for LLM to rank
        cand_text = "\n\n".join(
            f"--- CANDIDATE {i+1} ---\n"
            f"ID: {c['id']}\nName: {c.get('name')}\nCategory: {c.get('category')}\nTags: {', '.join(c.get('tags', []))}\n"
            f"Description: {c.get('description', '')}\n"
            f"Prompt:\n{c['prompt_text'][:800]}{'...' if len(c['prompt_text']) > 800 else ''}"
            for i, c in enumerate(candidates)
        )

        system = (
            "You are an expert prompt curator for software engineering AI agents. "
            "Your job is to select the MOST USEFUL mini-prompts from the candidates for the given task. "
            "Consider relevance to the task, generality vs specificity, and past usage signals if available."
        )

        user = f"""Current task / user request:
{task_description}

Additional context:
{context or "(none provided)"}

Available candidate mini-prompts:
{cand_text}

Task: Rank the top {top_k} most helpful mini-prompts for this task.
For each selected prompt, give:
- The ID
- A short "why it fits" (1 sentence)
- A relevance score 1-10

Return ONLY valid JSON in this exact format:
[
  {{"id": "...", "why": "...", "score": 9}},
  ...
]
Do not include any other text or explanation outside the JSON array."""

        try:
            raw = chat_completion_fn(
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                model=model,
                temperature=0.2,
            )
            # Try to extract JSON
            import re as _re
            json_match = _re.search(r"\[.*\]", raw, _re.DOTALL)
            if json_match:
                ranking = json.loads(json_match.group(0))
            else:
                ranking = json.loads(raw)

            # Merge ranking info back into candidates
            id_to_rank = {r["id"]: r for r in ranking if isinstance(r, dict) and "id" in r}
            enriched = []
            for c in candidates:
                if c["id"] in id_to_rank:
                    c = c.copy()
                    c["relevance_reason"] = id_to_rank[c["id"]].get("why", "")
                    c["relevance_score"] = id_to_rank[c["id"]].get("score", 5)
                    enriched.append(c)
            enriched.sort(key=lambda x: -x.get("relevance_score", 0))
            return enriched[:top_k]
        except Exception:
            # Fallback to keyword if LLM fails
            return candidates[:top_k]

    def get_context_injection(
        self,
        task_description: str,
        context: str = "",
        top_k: int = 3,
        chat_completion_fn: Optional[Callable] = None,
    ) -> str:
        """
        Returns a ready-to-inject string containing the best mini-prompts + guidance.
        Perfect for prepending to system prompt or adding to agent context.
        """
        best = self.select_best_for_context(
            task_description=task_description,
            context=context,
            top_k=top_k,
            chat_completion_fn=chat_completion_fn,
        )
        if not best:
            return ""

        parts = [
            "=== RELEVANT MINI-PROMPTS FROM YOUR PERSONAL LIBRARY ===\n"
            "Use the guidance below where it improves your response quality. "
            "Adapt, combine, or ignore as appropriate for the current task.\n"
        ]
        for i, p in enumerate(best, 1):
            reason = p.get("relevance_reason", "")
            parts.append(
                f"\n--- Prompt {i}: {p.get('name', p['id'])} (category: {p.get('category')}) ---\n"
                f"{p['prompt_text']}\n"
            )
            if reason:
                parts.append(f"[Why selected: {reason}]\n")
        parts.append("\n=== END MINI-PROMPTS ===\n")
        return "\n".join(parts)

    # --------------------------- Conversation Mining (New Feature) ---------------------------

    def mine_prompts_from_conversation(
        self,
        conversation: str | List[Dict[str, str]],
        chat_completion_fn: Callable,
        model: str = "default",
        max_candidates: int = 12,
        min_prompt_length: int = 45,
    ) -> List[Dict[str, Any]]:
        """
        NEW FEATURE: Search prior conversations for repeated or reusable mini-prompt patterns
        so you can quickly populate the library instead of manually copying them.

        Accepts either:
          - Raw conversation text (paste from Claude/Grok export, Markdown, etc.)
          - List of message dicts: [{"role": "user"|"assistant", "content": "..."}, ...]

        Uses the LLM to intelligently:
        - Find self-contained instructional blocks that look like mini-prompts
        - Detect repetition or high-value patterns you use often
        - Propose cleaned, canonical versions with suggested name, tags, category
        - Explain why each is worth saving

        Returns a list of candidate dicts ready for review. You can then call
        `save_mini_prompt(...)` on the ones you like (or pipe them through `improve_prompt`).
        """
        if not chat_completion_fn:
            raise ValueError("chat_completion_fn is required for mining")

        # Normalize input to plain text for the LLM
        if isinstance(conversation, list):
            text_parts = []
            for msg in conversation:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if content and len(content) > 20:
                    text_parts.append(f"[{role.upper()}]: {content}")
            conv_text = "\n\n".join(text_parts)
        else:
            conv_text = str(conversation)

        if len(conv_text) < 100:
            return []

        system_prompt = (
            "You are an expert prompt archaeologist and curator. "
            "Your job is to scan conversation history and extract high-value, reusable MINI-PROMPTS "
            "that the user (or AI) repeatedly relied on. Focus on short-to-medium instructional blocks "
            "that look like they were copy-pasted or re-used across tasks — things like role definitions, "
            "review checklists, coding standards, domain-specific rules (e.g. healthcare, async, security), etc.\n\n"
            "Ignore one-off instructions. Prioritize patterns that appear more than once or feel generalizable.\n\n"
            "For each good candidate you find, output a structured JSON object with:\n"
            "- suggested_name: short kebab-case or snake_case identifier\n"
            "- suggested_prompt_text: the cleaned, self-contained mini-prompt (remove conversation-specific parts)\n"
            "- suggested_category: one of [code-review, implementation, debugging, testing, refactoring, documentation, security, healthcare, general]\n"
            "- suggested_tags: array of 2-6 relevant lowercase tags\n"
            "- why_recommended: 1-sentence explanation of why this is worth saving to a personal library\n"
            "- original_snippet: the raw excerpt where it appeared (for traceability)\n\n"
            "Return ONLY a JSON array of such objects. No other text. Aim for the strongest 5-12 candidates."
        )

        user_prompt = f"""Here is the conversation history to mine:

{conv_text[:12000]}   # safety truncate

Extract the best reusable mini-prompt candidates now."""

        try:
            raw_output = chat_completion_fn(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model=model,
                temperature=0.3,
            )

            # Robust JSON extraction
            import re as _re
            json_match = _re.search(r"\[.*\]", raw_output, _re.DOTALL)
            if json_match:
                candidates = json.loads(json_match.group(0))
            else:
                candidates = json.loads(raw_output)

            # Post-process and filter
            cleaned = []
            seen_texts = set()
            for c in candidates:
                if not isinstance(c, dict):
                    continue
                text = c.get("suggested_prompt_text", "").strip()
                if len(text) < min_prompt_length:
                    continue
                if text in seen_texts:
                    continue
                seen_texts.add(text)

                cleaned.append({
                    "suggested_name": c.get("suggested_name", self._normalize_name(text[:60])),
                    "suggested_prompt_text": text,
                    "suggested_category": c.get("suggested_category", "general").lower(),
                    "suggested_tags": c.get("suggested_tags", []),
                    "why_recommended": c.get("why_recommended", ""),
                    "original_snippet": c.get("original_snippet", "")[:300],
                })

            return cleaned[:max_candidates]

        except Exception as e:
            # Return empty list on failure rather than crash
            print(f"[MiniPromptLib] Mining failed: {e}")
            return []

    # --------------------------- Improvement (Requirement 3) ---------------------------

    def improve_prompt(
        self,
        prompt_id: str,
        instructions: str = "Generalize this prompt, make it more robust across languages/frameworks, add guidance for edge cases, testing, and security where relevant. Keep it concise but high-signal.",
        chat_completion_fn: Optional[Callable] = None,
        model: str = "default",
        auto_save: bool = True,
    ) -> Dict[str, Any]:
        """
        Requirement #3: Use the underlying LLM to improve/generalize/strengthen a mini-prompt.

        Returns the improved entry (and saves new version if auto_save=True).
        """
        entry = self.get_prompt(prompt_id)
        if not entry:
            raise KeyError(f"Prompt '{prompt_id}' not found")

        if not chat_completion_fn:
            # No LLM provided — return current + instructions for manual improvement
            entry["improvement_suggestion"] = instructions
            return entry

        system = (
            "You are a world-class prompt engineer specializing in SWE AI agents. "
            "You improve mini-prompts so they are clearer, more generalizable, handle edge cases better, "
            "and produce higher quality outputs from coding LLMs. "
            "Preserve the original intent and voice while making surgical, high-impact improvements."
        )

        user = f"""Original mini-prompt (ID: {entry['id']}, Name: {entry.get('name')}):
{entry['prompt_text']}

Improvement goal / instructions from user:
{instructions}

Additional context about this prompt:
Category: {entry.get('category')}
Tags: {', '.join(entry.get('tags', []))}
Description: {entry.get('description', '')}
Previous usage stats: used {entry.get('usage_count', 0)} times, success rate ~{self._success_rate(entry):.0%}

Please output ONLY the improved mini-prompt text (nothing else). 
Make it excellent for use by coding agents like Claude, Grok, or local models."""

        try:
            improved_text = chat_completion_fn(
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                model=model,
                temperature=0.4,
            ).strip()

            # Create new versioned entry
            new_id = f"{entry['id']}_improved_{datetime.now().strftime('%Y%m%d_%H%M')}"
            new_entry = entry.copy()
            new_entry.update({
                "id": new_id,
                "prompt_text": improved_text,
                "description": entry.get("description", "") + " [IMPROVED VERSION]",
                "version": entry.get("version", 1) + 1,
                "created_at": self._now(),
                "last_used": None,
                "usage_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "notes": entry.get("notes", []) + [f"Improved from {entry['id']} with instructions: {instructions[:100]}..."],
            })

            if auto_save:
                self.prompts[new_id] = new_entry
                self._save()

            new_entry["was_improved_from"] = entry["id"]
            return new_entry
        except Exception as e:
            entry["improvement_error"] = str(e)
            return entry

    def _success_rate(self, entry: Dict) -> float:
        total = entry.get("success_count", 0) + entry.get("failure_count", 0)
        return entry.get("success_count", 0) / total if total > 0 else 0.5

    # --------------------------- Feedback & Self-Improvement (for Requirement 3 + long-term) ---------------------------

    def log_usage(
        self,
        prompt_id: str,
        success: Optional[bool] = None,
        notes: str = "",
    ) -> None:
        """
        Log that this prompt was used (and whether it helped).
        Enables the library to learn which prompts are effective.
        """
        entry = self.prompts.get(prompt_id) or self.get_prompt(prompt_id)
        if not entry:
            return
        pid = entry["id"]
        self.prompts[pid]["usage_count"] = self.prompts[pid].get("usage_count", 0) + 1
        self.prompts[pid]["last_used"] = self._now()
        if success is True:
            self.prompts[pid]["success_count"] = self.prompts[pid].get("success_count", 0) + 1
        elif success is False:
            self.prompts[pid]["failure_count"] = self.prompts[pid].get("failure_count", 0) + 1
        if notes:
            self.prompts[pid].setdefault("notes", []).append(
                f"{self._now()}: {notes}"
            )
        self._save()

    def record_selection(self, prompt_id: str) -> None:
        """Record an explicit navigator selection without claiming task success."""
        entry = self.prompts.get(prompt_id) or self.get_prompt(prompt_id)
        if not entry:
            raise KeyError(f"Prompt '{prompt_id}' not found")
        pid = entry["id"]
        self.prompts[pid]["selection_count"] = self.prompts[pid].get("selection_count", 0) + 1
        self.prompts[pid]["last_selected"] = self._now()
        self._save()

    def get_underperforming_prompts(self, min_usage: int = 3, success_threshold: float = 0.6) -> List[Dict[str, Any]]:
        """Find prompts that might benefit from improvement."""
        under = []
        for pid, entry in self.prompts.items():
            total = entry.get("success_count", 0) + entry.get("failure_count", 0)
            if total >= min_usage:
                rate = entry.get("success_count", 0) / total
                if rate < success_threshold:
                    under.append(entry.copy())
        return under

    # --------------------------- Helpers ---------------------------

    def _normalize_name(self, name: str) -> str:
        name = re.sub(r"[^a-zA-Z0-9_-]", "_", name.strip().lower())
        return re.sub(r"_+", "_", name)[:80]

    def _generate_id(self, prompt_text: str) -> str:
        # Short deterministic-ish ID from content
        h = str(hash(prompt_text[:200]))[-8:]
        return f"prompt_{h}"

    def export_library(self, path: str | Path) -> None:
        """Export full library (for backup or sharing)."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.prompts, f, indent=2)

    def import_library(self, path: str | Path, merge: bool = True) -> int:
        """Import prompts from another export. Returns number imported."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        count = 0
        for pid, entry in data.items():
            if merge and pid in self.prompts:
                continue
            self.prompts[pid] = entry
            count += 1
        self._save()
        return count

    def __len__(self) -> int:
        return len(self.prompts)

    def __repr__(self) -> str:
        return f"MiniPromptLibrary({len(self)} prompts, stored at {self.storage_path})"


# --------------------------- Convenience: Default chat wrapper examples ---------------------------

def make_ollama_chat_fn(host: str = "http://localhost:11434", default_model: str = "qwen2.5-coder:32b"):
    """
    Returns a chat_completion_fn compatible with MiniPromptLibrary using Ollama.
    Requires: pip install ollama   (or use requests)
    """
    try:
        import ollama
    except ImportError:
        raise ImportError("Install ollama package: pip install ollama")

    def _chat(messages: List[Dict[str, str]], model: str = default_model, temperature: float = 0.3) -> str:
        resp = ollama.chat(
            model=model,
            messages=messages,
            options={"temperature": temperature},
        )
        return resp["message"]["content"]

    return _chat


def make_openai_compatible_chat_fn(client: Any, default_model: str = "gpt-4o-mini"):
    """
    Wraps an OpenAI-compatible client (OpenAI, Grok via xAI, Together, etc.).
    Example:
        from openai import OpenAI
        client = OpenAI(base_url=..., api_key=...)
        fn = make_openai_compatible_chat_fn(client, "your-model")
    """
    def _chat(messages: List[Dict[str, str]], model: str = default_model, temperature: float = 0.3) -> str:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content

    return _chat
