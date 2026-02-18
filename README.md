# experience-engine

**A reflection-based memory layer for LLM apps.**
Your AI stops being reactive and starts being developmental.

Most AI apps have memory. This one has **experience**.

```
pip install experience-engine
```

---

## The Problem

Every conversation starts from zero. Your LLM doesn't know:
- What you've learned together
- How you tend to think
- Where your reasoning creates blind spots
- What contradictions exist in your goals

This package solves that with a two-layer pipeline:

```
Interactions → [Reflection] → Domain Beliefs (V1)
                                    ↓
              [Synthesis]  → Cognitive Patterns (V2)
                                    ↓
              [Chat]       → Context-aware responses
```

---

## Install

```bash
pip install experience-engine
```

**Requirements:** Python 3.10+ · [Ollama](https://ollama.ai) (local LLM)

```bash
ollama serve
ollama pull mistral   # or any model you prefer
```

Zero additional Python dependencies.

---

## Quickstart (20 lines)

```python
from experience_engine import (
    log_interaction,
    run_reflection,
    run_synthesis,
    format_cognitive_block,
    format_belief_block,
    apply_patterns,
)

# 1. Log interactions (call this after every LLM exchange)
log_interaction("What is karma yoga?", "Selfless action without attachment...")
log_interaction("Should I use cloud or local storage?", "Start local, scale later...")

# 2. Reflect: extract domain beliefs from the log
beliefs = run_reflection()
# → [{"belief": "User prefers local infrastructure", "confidence": 0.88, ...}]

# 3. Synthesize: extract cognitive patterns from beliefs
result = run_synthesis()
# → {"cognitive_patterns": [...], "decision_archetype": {"dominant": "control-first"}, ...}

# 4. Inject into your chat prompts
context = format_cognitive_block() + format_belief_block()
prompt  = context + "User: " + question

# 5. Apply patterns to new situations
analysis = apply_patterns("Should I use LangChain or build my own orchestration?")
```

---

## What V1 Produces (Beliefs)

```
[DOMAIN KNOWLEDGE]
██████████ 0.95  User is studying the Bhagavad Gita
              ↳ Asked about karma yoga and the three margas across multiple sessions

[VALUE]
█████████  0.90  User values ordered progression — strict sequence before expansion
              ↳ Corrected AI when it suggested learning all margas simultaneously
```

## What V2 Produces (Cognitive Patterns)

```
[COGNITIVE PATTERNS]

██████████ 0.91
Deterministic progression bias — masters step N before N+1, across all domains
  ↳ spiritual: Karma Marga → Jnana Marga as strict sequence
  ↳ technical: local build → scale later
  → Transfer: will prefer curriculum-style AI learning over exploratory access

█████████  0.85
Control-first architecture — optimizes for observability before throughput
  ↳ chose local files over cloud DB
  ↳ corrects AI to maintain precision of its own belief system

[DECISION ARCHETYPE]  ★ CONTROL-FIRST

████████████████████  52%  control-first
████████████          28%  depth-first
████                  12%  safety-first

[COGNITIVE TENSIONS]
⚡ 0.74 [HIGH]
A: Wants to build scalable AI systems
B: Avoids external dependencies, prefers local infrastructure
❓ Are you optimizing for control or scale in this phase?
```

---

## Before / After

**Without experience:**
> "You should consider using a managed vector database for your RAG system.
> Options include Pinecone, Weaviate, or Chroma."

**With experience:**
> "Your control-first archetype will resist Pinecone — and that instinct is right
> for now. Chroma local is the correct move. But note the tension: when you do
> need to scale, your aversion to managed services will slow you down. Set a
> concrete threshold now — '1M vectors' or '10ms p99 latency' — so the migration
> decision is already made before the pressure hits."

---

## Configuration

```python
from experience_engine import EngineConfig

config = EngineConfig(
    data_dir   = "experience",          # where to store logs and beliefs
    model      = "mistral",             # any Ollama model
    ollama_url = "http://localhost:11434/api/generate",
    reflection_window      = 50,        # interactions analyzed per reflection
    min_belief_confidence  = 0.6,       # beliefs below this are dropped
    min_pattern_confidence = 0.65,
)

# Pass config to any function
beliefs = run_reflection(config=config)
result  = run_synthesis(config=config)
```

Override with environment variables:
```bash
EXPERIENCE_DIR=./my_data EXPERIENCE_MODEL=llama3 python your_app.py
```

---

## CLI (after pip install)

```bash
experience-reflect              # log → beliefs
experience-synthesize           # beliefs → cognitive patterns
experience-show                 # display everything
experience-show --beliefs       # beliefs only
experience-show --tensions      # tensions only
experience-synthesize --transfer "I'm choosing a cloud provider"
experience-chat                 # interactive chat loop
```

---

## Bring Your Own LLM

Don't want Ollama? Pass any callable:

```python
def my_llm(prompt: str, temperature: float, config) -> str:
    # call OpenAI, Anthropic, llama.cpp, etc.
    return your_api_call(prompt, temperature)

beliefs = run_reflection(llm_fn=my_llm)
result  = run_synthesis(llm_fn=my_llm)
```

---

## File Structure

```
experience/
├── episodic_log.jsonl      ← append-only interaction log
├── beliefs.json            ← V1: domain beliefs
├── cognitive_patterns.json ← V2: cognitive signature + archetype
└── tensions.json           ← V2: active contradictions
```

All storage is plain JSON. No database. Inspect, edit, back up with standard tools.

---

## Roadmap

- [ ] Confidence decay (old patterns fade without reinforcement)
- [ ] Outcome tracking (did the advice work?)
- [ ] Tension resolution tracking
- [ ] Temporal archetype shift detection
- [ ] OpenAI / Anthropic adapters out of the box

---

## License

MIT
