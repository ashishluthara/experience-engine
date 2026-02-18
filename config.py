"""
config.py
---------
Central configuration. All paths and model settings in one place.
Override via environment variables or by passing config= to any public function.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class EngineConfig:
    # Storage — defaults to ./experience/ relative to CWD
    data_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("EXPERIENCE_DIR", "experience"))
    )

    # Ollama
    ollama_url: str = field(
        default_factory=lambda: os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
    )
    model: str = field(
        default_factory=lambda: os.environ.get("EXPERIENCE_MODEL", "mistral")
    )

    # Reflection settings
    reflection_window: int = 50       # how many recent interactions to analyze
    min_belief_confidence: float = 0.6

    # Synthesis settings
    synthesis_window: int = 200       # interactions fed into pattern synthesis
    min_pattern_confidence: float = 0.65

    # Response behavior
    context_window: int = 6           # conversation turns kept in prompt
    llm_temperature_chat: float = 0.7
    llm_temperature_reflect: float = 0.3
    llm_temperature_synthesize: float = 0.25
    llm_timeout: int = 180

    def __post_init__(self):
        self.data_dir = Path(self.data_dir)

    @property
    def log_file(self) -> Path:
        return self.data_dir / "episodic_log.jsonl"

    @property
    def belief_file(self) -> Path:
        return self.data_dir / "beliefs.json"

    @property
    def pattern_file(self) -> Path:
        return self.data_dir / "cognitive_patterns.json"

    @property
    def tension_file(self) -> Path:
        return self.data_dir / "tensions.json"

    def ensure_dirs(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)


# Module-level default — used when no config is passed
default_config = EngineConfig()
