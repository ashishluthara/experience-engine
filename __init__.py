"""
experience_engine
-----------------
A reflection-based memory layer for LLM apps.
Your AI stops being reactive and starts being developmental.

Public API (three entry points):

    log_interaction(question, answer, config?, extra_tags?) -> dict
    run_reflection(config?, llm_fn?, verbose?) -> list[dict]
    run_synthesis(config?, llm_fn?, verbose?) -> dict

Supporting functions:

    load_beliefs(config?) -> list[dict]
    load_patterns(config?) -> dict
    load_tensions(config?) -> list[dict]
    format_belief_block(beliefs?, config?) -> str
    format_cognitive_block(config?) -> str
    apply_patterns(situation, config?, llm_fn?) -> str

Configuration:

    EngineConfig(data_dir, model, ollama_url, ...)
    default_config   # module-level default, uses ./experience/ and mistral

Example:

    from experience_engine import log_interaction, run_reflection, run_synthesis

    # 1. Log your interactions
    log_interaction("What is karma yoga?", "Karma yoga is selfless action...")

    # 2. Reflect: extract domain beliefs from the log
    beliefs = run_reflection()

    # 3. Synthesize: extract cognitive patterns from beliefs
    result = run_synthesis()

    # 4. Inject context into your chat prompt
    from experience_engine import format_belief_block, format_cognitive_block
    prompt = format_cognitive_block() + format_belief_block() + "User: " + question
"""

from .config import EngineConfig, default_config

from .core import (
    log_interaction,
    load_log,
    log_count,
)

from .reflection import (
    run_reflection,
    load_beliefs,
    format_belief_block,
)

from .synthesis import (
    run_synthesis,
    load_patterns,
    load_tensions,
    format_cognitive_block,
    apply_patterns,
)

__version__ = "0.1.0"
__all__ = [
    # config
    "EngineConfig",
    "default_config",
    # core
    "log_interaction",
    "load_log",
    "log_count",
    # reflection (V1)
    "run_reflection",
    "load_beliefs",
    "format_belief_block",
    # synthesis (V2)
    "run_synthesis",
    "load_patterns",
    "load_tensions",
    "format_cognitive_block",
    "apply_patterns",
]
