"""
core.py
-------
Interaction logging — the foundation everything else reads from.

Public API:
    log_interaction(question, answer, config) -> dict
    load_log(n, config) -> list[dict]
"""

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .config import EngineConfig, default_config


# ── Auto-tagging ──────────────────────────────────────────────────────────────

_TAG_PATTERNS: dict[str, str] = {
    "infrastructure": r"\b(docker|k8s|kubernetes|nginx|server|deploy|cloud|aws|gcp|azure|local)\b",
    "ai_ml":          r"\b(llm|model|embedding|rag|vector|fine.?tun|inference|ollama|mistral|gpt)\b",
    "python":         r"\b(python|pip|venv|fastapi|flask|django|pydantic)\b",
    "architecture":   r"\b(architecture|design|pattern|scalab|microservice|monolith|system)\b",
    "debugging":      r"\b(error|bug|fix|broken|fail|crash|exception|traceback)\b",
    "preference":     r"\b(prefer|rather|instead|avoid|hate|love|like|dislike|want)\b",
    "goal":           r"\b(goal|want to|trying to|building|create|launch|ship)\b",
    "frustration":    r"\b(frustrat|annoy|slow|complic|overengineer|too much|wrong)\b",
    "spirituality":   r"\b(gita|krishna|karma|jnana|bhakti|dharma|marga|yoga|vedic|spiritual)\b",
    "correction":     r"\b(no,|wrong|incorrect|not right|that's not|actually,)\b",
    "investing":      r"\b(invest|stock|market|portfolio|value|p/e|dividend|equity|asset)\b",
    "learning":       r"\b(learn|study|understand|teach|master|curriculum|course|practice)\b",
}


def _auto_tag(text: str) -> list[str]:
    t = text.lower()
    return [tag for tag, pat in _TAG_PATTERNS.items() if re.search(pat, t)]


def _score_confidence(question: str, answer: str) -> float:
    """
    Heuristic confidence score based on hedging language density.
    Replace with LLM-based scoring if you need precision.
    """
    hedges = len(re.findall(
        r"\b(maybe|perhaps|might|could|not sure|unclear|depends|uncertain|possibly)\b",
        answer.lower(),
    ))
    length_ok = 50 < len(answer.split()) < 600
    return round(max(0.3, min(0.95, 0.85 - (hedges * 0.08) + (0.05 if length_ok else 0))), 2)


# ── Public API ────────────────────────────────────────────────────────────────

def log_interaction(
    question: str,
    answer: str,
    config: EngineConfig = default_config,
    extra_tags: list[str] | None = None,
) -> dict:
    """
    Append one interaction to the episodic log.

    Args:
        question:   the user's message
        answer:     the LLM's response
        config:     EngineConfig (uses default if not provided)
        extra_tags: additional tags to merge with auto-detected ones

    Returns:
        The logged entry as a dict.

    Example:
        from experience_engine import log_interaction
        entry = log_interaction("What is karma yoga?", "Karma yoga is...")
    """
    config.ensure_dirs()

    tags = _auto_tag(question + " " + answer)
    if extra_tags:
        tags = list(set(tags + extra_tags))

    entry = {
        "id":         str(uuid.uuid4())[:8],
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "question":   question,
        "answer":     answer,
        "tags":       tags,
        "confidence": _score_confidence(question, answer),
    }

    with config.log_file.open("a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def load_log(
    n: int | None = None,
    config: EngineConfig = default_config,
) -> list[dict]:
    """
    Load interaction log entries.

    Args:
        n:      how many recent entries to return (None = all)
        config: EngineConfig

    Returns:
        List of entry dicts, oldest first.
    """
    if not config.log_file.exists():
        return []
    lines = config.log_file.read_text().strip().splitlines()
    entries = [json.loads(l) for l in lines if l.strip()]
    return entries[-n:] if n else entries


def log_count(config: EngineConfig = default_config) -> int:
    """Return total number of logged interactions."""
    if not config.log_file.exists():
        return 0
    return sum(1 for l in config.log_file.open() if l.strip())
