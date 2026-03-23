"""Agentic disambiguation helpers for Wikidata entity linking."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .agentic_linking import AgenticLinkerTemplate
from .candidate_retrieval import EntityCandidate
from .wikidata import normalize_surface_form

DEFAULT_CLAUDE_MODEL = "haiku"

SYSTEM_PROMPT = """You are disambiguating a mention against a small Wikidata candidate set.

Choose the best candidate using the mention text and local context.
Return JSON only with:
- chosen_uri
- chosen_label
- confidence
- reasoning
"""


def detect_claude_cli_path() -> str | None:
    """Return the system Claude Code CLI path if available."""
    return shutil.which("claude")


def build_lexical_candidate_shortlist(
    mention: str,
    entities: list[dict[str, Any]],
    *,
    top_k: int = 5,
) -> list[EntityCandidate]:
    """Build a small candidate set without extra dependencies."""
    normalized_mention = normalize_surface_form(mention)
    mention_tokens = set(normalized_mention.split())
    ranked: list[EntityCandidate] = []

    for entity in entities:
        normalized_label = normalize_surface_form(entity["label"])
        label_tokens = set(normalized_label.split())
        overlap = len(mention_tokens & label_tokens)
        substring_bonus = 2 if normalized_mention in normalized_label else 0
        prefix_bonus = 1 if normalized_label.startswith(normalized_mention) else 0
        score = float(overlap + substring_bonus + prefix_bonus)
        if score <= 0:
            continue

        ranked.append(
            EntityCandidate(
                uri=entity["uri"],
                label=entity["label"],
                score=score,
                metadata={
                    "current_offices": entity.get("current_offices", []),
                    "wikidata_id": entity.get("metadata", {}).get("wikidata_id"),
                },
            )
        )

    return sorted(ranked, key=lambda candidate: (-candidate.score, candidate.label))[:top_k]


@dataclass
class AgenticDisambiguationResult:
    chosen_uri: str | None
    chosen_label: str | None
    confidence: str | None
    reasoning: str | None
    raw_response: str


async def disambiguate_with_claude_code(
    *,
    full_text: str,
    mention_text: str,
    start: int,
    end: int,
    candidates: list[EntityCandidate],
    model: str = DEFAULT_CLAUDE_MODEL,
    cwd: str | Path | None = None,
    cli_path: str | Path | None = None,
) -> AgenticDisambiguationResult:
    """Use Claude Code SDK for one-shot disambiguation."""
    try:
        from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query
    except ImportError as exc:
        raise RuntimeError(
            "claude-agent-sdk is not installed. Run: uv sync --extra agentic"
        ) from exc

    prompt_builder = AgenticLinkerTemplate()
    prompt = prompt_builder.build_prompt(
        full_text=full_text,
        mention_text=mention_text,
        start=start,
        end=end,
        candidates=candidates,
    )

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        cwd=str(cwd or Path.cwd()),
        cli_path=str(cli_path) if cli_path else detect_claude_cli_path(),
        permission_mode="default",
        model=model,
        max_turns=1,
        tools=[],
        allowed_tools=[],
    )

    response_text = ""
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    response_text += block.text

    parsed = parse_agentic_json_response(response_text)
    return AgenticDisambiguationResult(
        chosen_uri=parsed.get("chosen_uri"),
        chosen_label=parsed.get("chosen_label"),
        confidence=parsed.get("confidence"),
        reasoning=parsed.get("reasoning"),
        raw_response=response_text,
    )


def parse_agentic_json_response(response_text: str) -> dict[str, Any]:
    """Parse JSON returned by the agent, with a fenced-code fallback."""
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        if text.startswith("json"):
            text = text[4:].strip()
    return json.loads(text)
