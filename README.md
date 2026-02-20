# experience-engine

**A reflection-based memory layer for LLM apps.**
Your AI stops being reactive and starts being developmental.

Most AI apps have memory. This one has **experience**.

```bash
pip install experience-engine
```

---

## The Problem

Every conversation starts from zero. Your LLM doesn't know:
- What you've learned together
- How you tend to think
- Where your reasoning creates blind spots
- What contradictions exist in your goals

This package solves that with a three-layer pipeline:

```
Social Media + Chat Exports
        │
        ▼ experience-ingest
Raw Interactions (episodic_log.jsonl)
        │
        ▼ experience-reflect
Domain Beliefs (V1) — what you think
        │
        ▼ experience-synthesize
Cognitive Patterns (V2) — how you think
        │
        ▼ experience-chat
Context-aware responses tailored to your cognitive signature
```

---

## Install

```bash
pip install experience-engine
```

**Requirements:** Python 3.10+ · [Ollama](https://ollama.ai)

```bash
ollama serve
ollama pull mistral   # or any model you prefer
```

Zero additional Python dependencies.

---

## Quickstart

### Option A — Start from social media data (fastest way to build a profile)

```bash
# Step 1: Ingest your data
experience-ingest tweets.js --platform twitter
experience-ingest "WhatsApp Chat.txt" --platform whatsapp --user "Your Name"
experience-ingest posts.csv --platform linkedin_posts

# Step 2: Extract beliefs from your posts and messages
experience-reflect

# Step 3: Extract cognitive patterns from beliefs
experience-synthesize

# Step 4: See your cognitive signature
experience-show

# Step 5: Chat with full context
experience-chat
```

### Option B — Start from scratch via chat

```python
from experience_engine import log_interaction, run_reflection, run_synthesis

log_interaction("What is karma yoga?", "Selfless action without attachment...")
log_interaction("Should I use cloud or local storage?", "Start local, scale later...")

beliefs = run_reflection()
result  = run_synthesis()
```

---

## Social Media Ingestion

Export your data from any platform and feed it directly into the pipeline.
The engine reads your posts and messages, extracts how you think, and builds
your cognitive profile without you having to chat with it first.

### Supported Platforms

| Platform | Export format | How to export |
|---|---|---|
| WhatsApp | `.txt` | Chat → ⋮ → Export Chat |
| Twitter / X | `tweets.js` | Settings → Your Account → Download Archive |
| LinkedIn Posts | `posts.csv` | Settings → Data Privacy → Get a copy of your data |
| LinkedIn Messages | `messages.csv` | Settings → Data Privacy → Get a copy of your data |
| Instagram | `.json` | Settings → Your Activity → Download Your Information |
| Telegram | `result.json` | Desktop App → Settings → Export Telegram Data |
| Generic CSV | `.csv` | Any file with a text/content/message column |
| Generic JSON | `.json` | Any JSON array of posts or messages |

### CLI

```bash
# WhatsApp — provide your display name to identify your messages
experience-ingest "WhatsApp Chat.txt" --platform whatsapp --user "Ashish"

# Twitter — no user handle needed (all tweets are yours)
experience-ingest tweets.js --platform twitter

# LinkedIn
experience-ingest posts.csv --platform linkedin_posts
experience-ingest messages.csv --platform linkedin_messages --user "Ashish Luthara"

# Telegram
experience-ingest result.json --platform telegram --user "Ashish"

# Auto-detect platform from filename
experience-ingest tweets.js
experience-ingest "WhatsApp Chat.txt" --user "Ashish"
```

### Python API

```python
from experience_engine import ingest, ingest_file

# From a file
result = ingest_file("tweets.js", user_handle="ashishluthara")
print(result.summary())
# → [twitter] 847 ingested | 23 skipped | 870 total parsed

# From raw text
with open("WhatsApp Chat.txt") as f:
    result = ingest(f.read(), platform="whatsapp", user_handle="Ashish")
```

---

## What the Pipeline Produces

### V1 — Domain Beliefs

```
[DOMAIN KNOWLEDGE]
██████████ 0.95  User is deeply studying the Bhagavad Gita
              ↳ Multiple posts and questions about karma yoga, the three margas

[VALUE]
█████████  0.90  User values ordered progression — strict sequence before expansion
              ↳ Corrected AI when it suggested learning all margas simultaneously

[TECHNICAL PREFERENCE]
█████████  0.88  User prefers local infrastructure over cloud dependencies
              ↳ Consistent preference across WhatsApp messages and Twitter posts
```

### V2 — Cognitive Patterns

```
[COGNITIVE PATTERNS]

██████████ 0.91
Deterministic progression bias — masters step N before N+1, across all domains
  ↳ spiritual: Karma Marga → Jnana Marga as strict sequence
  ↳ technical: local build → scale later
  → Transfer: will prefer curriculum-style learning over exploratory access

█████████  0.85
Control-first architecture — optimizes for observability before throughput
  ↳ local Ollama over cloud APIs
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
> "You should consider using a managed vector database for your RAG system."

**With experience:**
> "Your control-first archetype will resist Pinecone — that instinct is right
> for now. Chroma local is the correct move. But set a concrete threshold now
> so the migration decision is already made before the pressure hits."

---

## CLI Reference

```bash
experience-ingest <file>  [--platform] [--user] [--data-dir]
experience-reflect        [--window N] [--data-dir]
experience-synthesize     [--transfer "situation"] [--data-dir]
experience-show           [--beliefs] [--patterns] [--tensions]
experience-chat           [--no-context] [--data-dir]
```

---

## Configuration

```python
from experience_engine import EngineConfig

config = EngineConfig(
    data_dir              = "experience",
    model                 = "mistral",
    reflection_window     = 50,
    min_belief_confidence = 0.6,
)
```

Override with environment variables:
```bash
EXPERIENCE_DIR=./my_data EXPERIENCE_MODEL=llama3 python your_app.py
```

---

## Bring Your Own LLM

```python
def my_llm(prompt: str, temperature: float, config) -> str:
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

Plain JSON. No database. Inspect, edit, back up with standard tools.

---

## Roadmap

- [x] Reflection-based belief extraction (V1)
- [x] Cognitive pattern synthesis (V2)
- [x] Social media ingestion (WhatsApp, Twitter, LinkedIn, Instagram, Telegram)
- [x] Relevance gate (context only injected when question warrants it)
- [ ] Confidence decay (old patterns fade without reinforcement)
- [ ] Outcome tracking (did the advice work?)
- [ ] Tension resolution tracking
- [ ] Temporal archetype shift detection
- [ ] OpenAI / Anthropic adapters

---

## License

MIT
