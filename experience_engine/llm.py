"""
llm.py
------
Single adapter for all LLM calls. Swap model/backend here without touching
reflection or synthesis logic.

To use a different backend (OpenAI-compatible, llama.cpp, etc.):
  override call() with your own function and pass it as llm_fn= to any engine.
"""

import json
import urllib.request
from typing import Callable

from .config import EngineConfig, default_config


def call(
    prompt: str,
    temperature: float = 0.5,
    config: EngineConfig = default_config,
) -> str:
    """
    Call the configured local LLM. Returns response text.
    Raises RuntimeError with a clear message if Ollama is unreachable.
    """
    payload = json.dumps({
        "model":   config.model,
        "prompt":  prompt,
        "stream":  False,
        "options": {
            "temperature": temperature,
            "num_ctx":     4096,
        },
    }).encode()

    req = urllib.request.Request(
        config.ollama_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=config.llm_timeout) as resp:
            return json.loads(resp.read())["response"]
    except Exception as exc:
        raise RuntimeError(
            f"LLM call failed ({exc}).\n"
            f"Make sure Ollama is running:  ollama serve\n"
            f"Pull the model if needed:     ollama pull {config.model}"
        ) from exc


# Type alias — any function with the same signature can replace call()
LLMCallable = Callable[[str, float, EngineConfig], str]
