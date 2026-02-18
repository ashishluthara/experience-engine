"""
synthesis.py
------------
V2: Extract cross-domain cognitive patterns from beliefs.

Public API:
    run_synthesis(config, llm_fn) -> dict        full synthesis result
    load_patterns(config) -> dict
    load_tensions(config) -> list[dict]
    format_cognitive_block(config) -> str        prompt-ready string
"""

import json
import re
from datetime import datetime, timezone

from .config import EngineConfig, default_config
from .core import load_log, log_count
from .reflection import load_beliefs
from . import llm as _llm


_ARCHETYPES = [
    "control-first", "scale-first", "research-first",
    "execution-first", "safety-first", "depth-first", "simplicity-first",
]

# ── Storage ───────────────────────────────────────────────────────────────────

def load_patterns(config: EngineConfig = default_config) -> dict:
    if not config.pattern_file.exists():
        return {
            "last_updated": None, "synthesis_count": 0,
            "abstraction_ladder": {"observations": [], "themes": [], "patterns": [], "biases": []},
            "cognitive_patterns": [],
            "decision_archetype": {"dominant": None, "distribution": {}, "history": []},
            "experience_compression": {"total_events": 0, "total_patterns": 0, "compression_ratio": None},
        }
    return json.loads(config.pattern_file.read_text())


def load_tensions(config: EngineConfig = default_config) -> list[dict]:
    if not config.tension_file.exists():
        return []
    return json.loads(config.tension_file.read_text()).get("tensions", [])


def _save_synthesis(result: dict, synthesis_count: int, total_events: int, config: EngineConfig):
    patterns     = result.get("cognitive_patterns", [])
    tensions     = result.get("tensions", [])
    archetype    = result.get("decision_archetype", {})
    ladder       = result.get("abstraction_ladder", {})

    pattern_data = {
        "last_updated":      datetime.now(timezone.utc).isoformat(),
        "synthesis_count":   synthesis_count,
        "abstraction_ladder": ladder,
        "cognitive_patterns": patterns,
        "decision_archetype": archetype,
        "experience_compression": {
            "total_events":    total_events,
            "total_patterns":  len(patterns),
            "compression_ratio": f"{total_events}:{len(patterns)}" if patterns else "N/A",
        },
    }
    config.pattern_file.write_text(json.dumps(pattern_data, indent=2))

    tension_data = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "tensions":     tensions,
        "resolved":     [],
    }
    config.tension_file.write_text(json.dumps(tension_data, indent=2))


# ── Prompt ────────────────────────────────────────────────────────────────────

_SYNTHESIS_PROMPT = """\
You are a cognitive pattern analyst. You do not analyze WHAT someone thinks.
You analyze HOW they think — their cognitive signature across all domains.

## Domain Beliefs (V1 output)
{beliefs}

## Interaction Count
{log_count} total interactions logged.

## Task
Return a single JSON object with these exact keys:

"abstraction_ladder": {{
  "observations": [3-6 specific behavioral observations],
  "themes":       [2-4 recurring cross-domain themes],
  "patterns":     [2-3 domain-agnostic cognitive patterns],
  "biases":       [1-2 potential blind spots]
}}

"cognitive_patterns": [
  {{
    "pattern":               "precise, domain-agnostic behavioral statement",
    "confidence":            float 0.0-1.0,
    "cross_domain_evidence": ["example from domain A", "example from domain B"],
    "transfer_hypothesis":   "one sentence predicting behavior in a new unseen domain"
  }}
]

"decision_archetype": {{
  "dominant":     "one of: {archetypes}",
  "distribution": {{"archetype_name": weight_float, ...}}  // must sum to 1.0
}}

"tensions": [
  {{
    "belief_a":         "first conflicting belief",
    "belief_b":         "second conflicting belief",
    "tension":          "why they conflict (1-2 sentences)",
    "strategic_question": "the exact question to resolve the tension",
    "severity":         float 0.0-1.0
  }}
]

Hard rules:
- Patterns MUST be cross-domain. Single-domain = belief, not pattern.
- "User prefers X" is NOT a pattern. "User applies X-reasoning across Y and Z" IS.
- Return ONLY the JSON object. No markdown. No explanation.
"""


def _parse_result(raw: str) -> dict:
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    try:
        return json.loads(raw)
    except Exception:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {}


# ── Public API ────────────────────────────────────────────────────────────────

def run_synthesis(
    config: EngineConfig = default_config,
    llm_fn=None,
    verbose: bool = True,
) -> dict:
    """
    Read beliefs → extract cognitive patterns → update cognitive_patterns.json + tensions.json.

    Run run_reflection() first — synthesis reads from beliefs.json.

    Args:
        config:  EngineConfig
        llm_fn:  optional replacement LLM callable
        verbose: print progress to stdout

    Returns:
        Full synthesis result dict with keys:
        abstraction_ladder, cognitive_patterns, decision_archetype, tensions

    Example:
        from experience_engine import run_synthesis
        result = run_synthesis()
        for p in result["cognitive_patterns"]:
            print(p["pattern"], p["confidence"])
    """
    _call = llm_fn or _llm.call

    beliefs = load_beliefs(config)
    if not beliefs:
        if verbose:
            print("[synthesis] No beliefs found. Run run_reflection() first.")
        return {}

    total_events  = log_count(config)
    existing      = load_patterns(config)
    synth_count   = existing.get("synthesis_count", 0)

    if verbose:
        print(f"[synthesis] Synthesizing from {len(beliefs)} beliefs, {total_events} interactions…")

    prompt = _SYNTHESIS_PROMPT.format(
        beliefs=json.dumps(beliefs, indent=2),
        log_count=total_events,
        archetypes=", ".join(_ARCHETYPES),
    )

    raw    = _call(prompt, temperature=config.llm_temperature_synthesize, config=config)
    result = _parse_result(raw)

    if not result:
        if verbose:
            print("[synthesis] Parsing failed — check LLM output.")
        return {}

    _save_synthesis(result, synth_count + 1, total_events, config)

    n_patterns = len(result.get("cognitive_patterns", []))
    n_tensions = len(result.get("tensions", []))
    if verbose:
        print(f"[synthesis] ✓ {n_patterns} patterns, {n_tensions} tensions saved.")

    return result


def apply_patterns(
    situation: str,
    config: EngineConfig = default_config,
    llm_fn=None,
) -> str:
    """
    Transfer cognitive patterns to a new situation.

    Args:
        situation: description of the new decision or context
        config:    EngineConfig
        llm_fn:    optional replacement LLM callable

    Returns:
        Pattern-aware analysis string.

    Example:
        from experience_engine import apply_patterns
        analysis = apply_patterns("Should I use LangChain or build my own orchestration?")
        print(analysis)
    """
    _call = llm_fn or _llm.call
    patterns_data = load_patterns(config)
    patterns      = patterns_data.get("cognitive_patterns", [])
    archetype     = patterns_data.get("decision_archetype", {}).get("dominant", "unknown")

    if not patterns:
        return "No cognitive patterns available. Run run_synthesis() first."

    prompt = f"""\
You are an AI advisor with deep knowledge of this user's cognitive patterns.

## Cognitive Patterns
{json.dumps(patterns, indent=2)}

## Dominant Archetype: {archetype}

## New Situation
{situation}

Apply the user's cognitive patterns to this situation.
Name which patterns are relevant. Predict their instinct.
Flag if their instinct contradicts their archetype.
Give a direct recommendation in their cognitive style.
Write in prose. No lists. Be specific. Four to eight sentences.
"""
    return _call(prompt, temperature=0.5, config=config)


# ── Prompt injection ──────────────────────────────────────────────────────────

def format_cognitive_block(config: EngineConfig = default_config) -> str:
    """
    Return a prompt-ready string of cognitive patterns for chat prompt injection.

    Returns empty string if no synthesis has been run yet.
    """
    patterns_data = load_patterns(config)
    tensions      = load_tensions(config)

    patterns  = patterns_data.get("cognitive_patterns", [])
    archetype = patterns_data.get("decision_archetype", {})

    if not patterns:
        return ""

    lines = ["## Cognitive Signature (how this user thinks)\n"]
    for p in sorted(patterns, key=lambda x: -x.get("confidence", 0)):
        lines.append(f"- {p['pattern']} ({p['confidence']:.0%})")

    if archetype.get("dominant"):
        lines.append(f"\nDominant decision archetype: {archetype['dominant']}")

    active_tensions = [t for t in tensions if t.get("severity", 0) > 0.5]
    if active_tensions:
        lines.append("\nActive cognitive tensions:")
        for t in active_tensions:
            lines.append(f"- {t['strategic_question']}")

    lines.append(
        "\nWhen responding: align with cognitive style. "
        "Flag contradictions to archetype. "
        "Apply cross-domain transfer when relevant. "
        "No lists. Direct prose only. Name patterns by label.\n"
    )
    return "\n".join(lines)
