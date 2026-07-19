"""Stateful, progressive prompt navigation built on the shared ranker."""

from __future__ import annotations

from .models import ContextPacket, NavigationSession, RankedPrompt
from .ranking import page_ranked_prompts, rank_prompts


class InvalidChoiceError(ValueError):
    """Raised when a user chooses a number that is not on the current page."""


class WorkflowNavigator:
    """Navigate a prompt library in small contextual pages."""

    def __init__(self, library):
        self.library = library

    def start(self, packet: ContextPacket) -> NavigationSession:
        ranked = rank_prompts(packet, self.library.list_prompts(limit=1000))
        return NavigationSession(packet=packet, ranked=ranked, selected_prompt_ids=list(packet.selected_prompt_ids))

    def current_page(self, session: NavigationSession) -> list[RankedPrompt]:
        return page_ranked_prompts(session.ranked, offset=session.offset)

    def more(self, session: NavigationSession) -> list[RankedPrompt]:
        next_offset = session.offset + 3
        if next_offset < len(session.ranked):
            session.offset = next_offset
        return self.current_page(session)

    def can_more(self, session: NavigationSession) -> bool:
        """Return whether the session has another non-empty small page."""
        return session.offset + 3 < len(session.ranked)

    def try_again(self, session: NavigationSession, packet: ContextPacket) -> NavigationSession:
        session.packet = packet
        session.ranked = rank_prompts(packet, self.library.list_prompts(limit=1000))
        session.offset = 0
        return session

    def select(self, session: NavigationSession, choice: int) -> RankedPrompt:
        page = self.current_page(session)
        index = choice - 1
        if index < 0 or index >= len(page):
            raise InvalidChoiceError(f"Choose a number from 1 to {len(page)}.")
        selected = page[index]
        self.library.record_selection(selected.prompt_id)
        if selected.prompt_id not in session.selected_prompt_ids:
            session.selected_prompt_ids.append(selected.prompt_id)
        return selected

    def nested_page(self, session: NavigationSession) -> list[RankedPrompt]:
        """Offer another small layer without repeating selected prompt IDs."""
        remaining = [
            prompt
            for prompt in self.library.list_prompts(limit=1000)
            if prompt["id"] not in session.selected_prompt_ids
        ]
        session.ranked = rank_prompts(session.packet, remaining)
        session.offset = 0
        return self.current_page(session)

    def back(self, session: NavigationSession) -> NavigationSession:
        if session.selected_prompt_ids:
            session.selected_prompt_ids.pop()
            session.ranked = rank_prompts(session.packet, self.library.list_prompts(limit=1000))
            session.offset = 0
        return session

    def composition_preview(self, session: NavigationSession) -> str:
        prompts = [self.library.get_prompt(prompt_id) for prompt_id in session.selected_prompt_ids]
        texts = [prompt["prompt_text"] for prompt in prompts if prompt]
        return "\n\n".join(texts)
