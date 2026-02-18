"""
reflection.py
-------------
V1: Extract domain beliefs from the interaction log.

Public API:
    run_reflection(config, llm_fn) -> list[dict]   beliefs extracted
    load_beliefs(config) -> list[dict]
    format_belief_block(beliefs) -> str            prompt-ready string
"""

import json
import re
from datetime import datetime, timezone

from .config import EngineConfig, default_config
from .core import load_log
from . import llm as _llm


# ── Storage ───────────────────────────────────────────────────────────────────

def load_beliefs(config: EngineConfig = default_config) -> list[dict]:
    """Load current beliefs from disk."""
    if not config.belief_file.exists():
        return []
    return json.loads(config.belief_file.read_text()).get("beliefs", [])


def _save_beliefs(beliefs: list[dict], reflection_count: int, config: EngineConfig):
    data = {
        "last_updated":     datetime.now(timezone.utc).isoformat(),
        "reflection_count": reflection_count,
        "beliefs":          beliefs,
    }
    config.belief_file.write_text(json.dumps(data, indent=2))


# ── Prompt ────────────────────────────────────────────────────────────────────

_REFLECTION_PROMPT = """\
You are a reflection engine. Analyze AI-user interactions and extract durable beliefs
about the user — their goals, preferences, working style, and recurring frustrations.

## Interactions (most recent {n} sessions)
{interactions}

## Existing Beliefs
{existing}

## Task
Return a JSON array of belief objects. Each must have:
  - "belief":      a clear, specific statement about the user (string)
  - "confidence":  float 0.0–1.0
  - "evidence":    1–2 sentence summary of supporting evidence (string)
  - "category":    one of: goal | technical_preference | working_style |
                   frustration | domain_knowledge | value

Rules:
1. Update confidence on existing beliefs if new evidence supports or contradicts.
2. Add new beliefs only if supported by at least 2 interactions.
3. Exclude beliefs with confidence < {min_conf}.
4. Be specific — "prefers Python" > "likes coding".
5. Return ONLY the JSON array. No explanation. No markdown fences.
"""


def _format_interactions(entries: list[dict]) -> str:
    parts = []
    for i, e in enumerate(entries, 1):
        tags = ", ".join(e.get("tags", []))
        answer_preview = e["answer"][:300] + ("…" if len(e["answer"]) > 300 else "")
        parts.append(
            f"[{i}] Q: {e['question']}\n"
            f"     A: {answer_preview}\n"
            f"     Tags: {tags} | Confidence: {e.get('confidence', '?')}"
        )
    return "\n\n".join(parts)


def _parse_beliefs(raw: str) -> list[dict]:
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return []


# ── Public API ────────────────────────────────────────────────────────────────

def run_reflection(
    config: EngineConfig = default_config,
    llm_fn=None,
    verbose: bool = True,
) -> list[dict]:
    """
    Read recent interactions → extract beliefs → update beliefs.json.

    Args:
        config:  EngineConfig
        llm_fn:  optional replacement LLM callable (for testing/custom backends)
        verbose: print progress to stdout

    Returns:
        List of updated belief dicts.

    Example:
        from experience_engine import run_reflection
        beliefs = run_reflection()
        for b in beliefs:
            print(b["belief"], b["confidence"])
    """
    _call = llm_fn or _llm.call

    entries = load_log(n=config.reflection_window, config=config)
    if not entries:
        if verbose:
            print("[reflection] No interactions logged yet.")
        return []

    existing = load_beliefs(config)

    # load reflection count from disk
    reflection_count = 0
    if config.belief_file.exists():
        reflection_count = json.loads(config.belief_file.read_text()).get("reflection_count", 0)

    if verbose:
        print(f"[reflection] Analyzing {len(entries)} interactions…")

    prompt = _REFLECTION_PROMPT.format(
        n=len(entries),
        interactions=_format_interactions(entries),
        existing=json.dumps(existing, indent=2) if existing else "None yet.",
        min_conf=config.min_belief_confidence,
    )

    raw = _call(prompt, temperature=config.llm_temperature_reflect, config=config)
    beliefs = _parse_beliefs(raw)
    filtered = [b for b in beliefs if b.get("confidence", 0) >= config.min_belief_confidence]

    _save_beliefs(filtered, reflection_count + 1, config)

    if verbose:
        print(f"[reflection] ✓ {len(filtered)} beliefs saved.")

    return filtered


# ── Prompt injection ──────────────────────────────────────────────────────────

def format_belief_block(
    beliefs: list[dict] | None = None,
    config: EngineConfig = default_config,
) -> str:
    """
    Return a prompt-ready string of current beliefs for injection into chat prompts.

    Args:
        beliefs: pass beliefs directly, or leave None to load from disk
        config:  EngineConfig

    Returns:
        Formatted string block, empty string if no beliefs exist.
    """
    if beliefs is None:
        beliefs = load_beliefs(config)
    if not beliefs:
        return ""
    lines = ["## What I know about you (domain beliefs)\n"]
    for b in sorted(beliefs, key=lambda x: -x.get("confidence", 0)):
        lines.append(f"- {b['belief']} ({b.get('confidence', 0):.0%})")
    return "\n".join(lines) + "\n\n"
