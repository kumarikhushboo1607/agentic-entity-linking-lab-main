"""Context-driven agentic linking templates for Wikidata experiments."""

from __future__ import annotations

from typing import Any, Callable

from .candidate_retrieval import EntityCandidate


def extract_context_window(text: str, start: int, end: int, window: int = 120) -> dict[str, str]:
    """Extract left and right context around a mention span."""
    left = text[max(0, start - window):start]
    right = text[end:min(len(text), end + window)]
    return {"left_context": left, "right_context": right}


class AgenticLinkerTemplate:
    """A context-driven linker scaffold modeled after the SNOMED project's agentic stage.

    The harness is backend-agnostic: students pass a callable that receives a prompt
    and returns structured output from OpenAI, Anthropic, Ollama, or another client.
    """

    system_prompt = """You are linking mentions in text to Wikidata entities.

Use the mention text, surrounding context, and candidate list to choose the best URI.
Prefer the highest-scoring candidate unless context clearly supports another choice.
Return JSON with:
- chosen_uri
- confidence
- reasoning
"""

    def build_prompt(
        self,
        *,
        full_text: str,
        mention_text: str,
        start: int,
        end: int,
        candidates: list[EntityCandidate],
    ) -> str:
        context = extract_context_window(full_text, start, end)
        lines = [
            "Task: link one mention to the best Wikidata entity.",
            f"Mention: {mention_text}",
            f"Span: {start}-{end}",
            f"Context: ...{context['left_context']}[{mention_text}]{context['right_context']}...",
            "",
            "Candidates:",
        ]

        for index, candidate in enumerate(candidates, start=1):
            lines.append(
                f"{index}. {candidate.label} | {candidate.uri} | score={candidate.score:.4f} | "
                f"offices={', '.join(candidate.metadata.get('current_offices', []))}"
            )

        lines.append("")
        lines.append("Return JSON only.")
        return "\n".join(lines)

    def link_with_llm(
        self,
        *,
        full_text: str,
        mention_text: str,
        start: int,
        end: int,
        candidates: list[EntityCandidate],
        llm_call: Callable[[str, str], dict[str, Any]],
    ) -> dict[str, Any]:
        prompt = self.build_prompt(
            full_text=full_text,
            mention_text=mention_text,
            start=start,
            end=end,
            candidates=candidates,
        )
        return llm_call(self.system_prompt, prompt)
