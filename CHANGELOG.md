# Changelog

## v0.2.0 — Social Media Ingestion

### Added
- `experience-ingest` CLI command — ingest social media exports directly into the pipeline
- `ingest()` and `ingest_file()` public API functions
- Platform support: WhatsApp, Twitter/X, LinkedIn (posts + messages), Instagram, Telegram, generic CSV/JSON
- Auto-detection of platform from filename
- `IngestResult` dataclass with ingestion summary stats

### Fixed
- Relevance gate in `cmd_chat()` — cognitive context no longer injected on greetings or short social messages
- Tightened `SYSTEM` prompt to prevent unprompted personality analysis

### Changed
- Version bump: `0.1.0` → `0.2.0`

---

## v0.1.0 — Initial Release

### Added
- `log_interaction()` — append interactions to episodic log with auto-tagging and confidence scoring
- `run_reflection()` — V1: extract domain beliefs from interaction log
- `run_synthesis()` — V2: extract cross-domain cognitive patterns, decision archetype, and tensions
- `format_belief_block()` / `format_cognitive_block()` — prompt injection helpers
- `apply_patterns()` — transfer cognitive patterns to new situations
- `EngineConfig` — centralized configuration with env var overrides
- CLI commands: `experience-reflect`, `experience-synthesize`, `experience-show`, `experience-chat`
- Bring Your Own LLM support via `llm_fn=` parameter
- Zero pip dependencies beyond the package itself
