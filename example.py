"""
example.py
----------
The full Experience Engine pipeline in 20 lines.
This is your README demo.

Prerequisites:
    ollama serve
    ollama pull mistral
"""

import sys
sys.path.insert(0, ".")   # remove this line after: pip install experience-engine

from experience_engine import (
    log_interaction,
    run_reflection,
    run_synthesis,
    format_cognitive_block,
    format_belief_block,
    apply_patterns,
    EngineConfig,
)

# Optional: use a custom data directory or model
config = EngineConfig(data_dir="experience", model="mistral")

# ── Step 1: Log some interactions ─────────────────────────────────────────────
print("Step 1: Logging interactions…")
log_interaction("What is the main teaching of the Bhagavad Gita?",
                "Selfless action (nishkama karma) — do your duty without attachment to results.",
                config=config)

log_interaction("What are the three margas?",
                "Karma Marga (action), Jnana Marga (knowledge), Bhakti Marga (devotion).",
                config=config)

log_interaction("Should I use a cloud database or local files for my AI system?",
                "Given your preference for control, start local. Postgres when you hit real scale.",
                config=config)

log_interaction("Should I learn all three margas simultaneously?",
                "You can explore all three, but many teachers recommend starting with Karma Marga.",
                config=config)

# ── Step 2: Reflect — extract domain beliefs ───────────────────────────────────
print("\nStep 2: Reflecting…")
beliefs = run_reflection(config=config)

# ── Step 3: Synthesize — extract cognitive patterns ────────────────────────────
print("\nStep 3: Synthesizing cognitive patterns…")
result = run_synthesis(config=config)

# ── Step 4: Show what gets injected into every prompt ─────────────────────────
print("\nStep 4: Context injected into every future prompt:")
print("─" * 60)
print(format_cognitive_block(config))
print(format_belief_block(config=config))

# ── Step 5: Transfer — apply patterns to a new situation ──────────────────────
print("Step 5: Transfer engine — new domain, same cognitive patterns:")
print("─" * 60)
analysis = apply_patterns(
    "I'm deciding whether to use LangChain or build my own LLM orchestration layer.",
    config=config,
)
print(analysis)
