"""
cli.py
------
Entry points for installed CLI commands:

    experience-reflect      run V1 reflection
    experience-synthesize   run V2 synthesis
    experience-show         display current state
    experience-chat         interactive chat loop
"""

import argparse
import json
import sys

from .config import EngineConfig, default_config
from .core import log_count
from .reflection import run_reflection, load_beliefs
from .synthesis import run_synthesis, load_patterns, load_tensions, apply_patterns


# ── Shared display ─────────────────────────────────────────────────────────────

def _bar(conf: float, width: int = 10) -> str:
    return "█" * round(conf * width)


def _display_beliefs(beliefs: list[dict]):
    if not beliefs:
        print("  No beliefs yet. Run: experience-reflect")
        return
    by_cat: dict[str, list] = {}
    for b in beliefs:
        by_cat.setdefault(b.get("category", "other"), []).append(b)
    for cat, items in sorted(by_cat.items()):
        print(f"\n  [{cat.upper().replace('_',' ')}]")
        for b in sorted(items, key=lambda x: -x.get("confidence", 0)):
            print(f"  {_bar(b['confidence']):<10} {b['confidence']:.2f}  {b['belief']}")
            if b.get("evidence"):
                print(f"             ↳ {b['evidence']}")


def _display_patterns(patterns_data: dict, tensions: list[dict]):
    ladder  = patterns_data.get("abstraction_ladder", {})
    cp      = patterns_data.get("cognitive_patterns", [])
    arch    = patterns_data.get("decision_archetype", {})
    ec      = patterns_data.get("experience_compression", {})
    synth_n = patterns_data.get("synthesis_count", 0)

    print(f"\n{'═'*64}")
    print(f"  COGNITIVE SIGNATURE  (synthesis #{synth_n})")
    print(f"{'═'*64}")

    if any(ladder.values()):
        print("\n  [ABSTRACTION LADDER]")
        for key, label in [("observations","L1 Observations"),("themes","L2 Themes"),
                           ("patterns","L3 Patterns"),("biases","L4 Biases")]:
            for item in ladder.get(key, []):
                print(f"    {label[:2]}: {item}")

    if cp:
        print("\n  [COGNITIVE PATTERNS]")
        for p in sorted(cp, key=lambda x: -x.get("confidence", 0)):
            print(f"\n  {_bar(p['confidence']):<10} {p['confidence']:.2f}")
            print(f"  {p['pattern']}")
            for ev in p.get("cross_domain_evidence", []):
                print(f"    ↳ {ev}")
            if p.get("transfer_hypothesis"):
                print(f"    → {p['transfer_hypothesis']}")

    if arch.get("dominant"):
        print(f"\n  [DECISION ARCHETYPE]  ★ {arch['dominant'].upper()}")
        for name, w in sorted(arch.get("distribution", {}).items(), key=lambda x: -x[1]):
            print(f"  {_bar(w, 20):<20} {w:.0%}  {name}")

    if ec.get("compression_ratio"):
        print(f"\n  [COMPRESSION]  {ec['total_events']} events → {ec['total_patterns']} patterns  ({ec['compression_ratio']})")

    if tensions:
        print(f"\n  [TENSIONS]")
        for t in sorted(tensions, key=lambda x: -x.get("severity", 0)):
            sev = t.get("severity", 0)
            label = "HIGH" if sev > 0.7 else "MED" if sev > 0.4 else "LOW"
            print(f"\n  ⚡ {sev:.2f} [{label}]  {t['tension']}")
            print(f"     A: {t['belief_a']}")
            print(f"     B: {t['belief_b']}")
            print(f"  ❓ {t['strategic_question']}")
    print()


# ── CLI commands ───────────────────────────────────────────────────────────────

def cmd_reflect():
    parser = argparse.ArgumentParser(description="Run V1 reflection: log → beliefs")
    parser.add_argument("--data-dir", default="experience", help="data directory path")
    parser.add_argument("--model",    default="mistral",    help="Ollama model name")
    parser.add_argument("--window",   type=int, default=50, help="interactions to analyze")
    args = parser.parse_args()

    config = EngineConfig(data_dir=args.data_dir, model=args.model)
    config.reflection_window = args.window
    beliefs = run_reflection(config=config)
    _display_beliefs(beliefs)


def cmd_synthesize():
    parser = argparse.ArgumentParser(description="Run V2 synthesis: beliefs → cognitive patterns")
    parser.add_argument("--data-dir", default="experience", help="data directory path")
    parser.add_argument("--model",    default="mistral",    help="Ollama model name")
    parser.add_argument("--transfer", type=str, default=None, help="apply patterns to situation")
    args = parser.parse_args()

    config = EngineConfig(data_dir=args.data_dir, model=args.model)

    if args.transfer:
        print(f"\n[Transfer → {args.transfer}]\n")
        print(apply_patterns(args.transfer, config=config))
        return

    result = run_synthesis(config=config)
    if result:
        _display_patterns(load_patterns(config), load_tensions(config))


def cmd_show():
    parser = argparse.ArgumentParser(description="Display current beliefs and patterns")
    parser.add_argument("--data-dir",  default="experience", help="data directory path")
    parser.add_argument("--beliefs",   action="store_true",  help="show beliefs only")
    parser.add_argument("--patterns",  action="store_true",  help="show patterns only")
    parser.add_argument("--tensions",  action="store_true",  help="show tensions only")
    args = parser.parse_args()

    config   = EngineConfig(data_dir=args.data_dir)
    beliefs  = load_beliefs(config)
    patterns = load_patterns(config)
    tensions = load_tensions(config)

    show_all = not (args.beliefs or args.patterns or args.tensions)

    if args.beliefs or show_all:
        print(f"\n{'═'*64}")
        print(f"  V1 BELIEFS  ({len(beliefs)} total | {log_count(config)} interactions logged)")
        print("═"*64)
        _display_beliefs(beliefs)

    if args.patterns or args.tensions or show_all:
        _display_patterns(patterns, tensions if (args.tensions or show_all) else [])



def cmd_ingest():
    """Ingest social media exports into the experience log."""
    import argparse as _ap
    parser = _ap.ArgumentParser(description="Ingest social media exports")
    parser.add_argument("file",       help="path to the export file")
    parser.add_argument("--platform", default=None,         help="platform name (auto-detected if omitted)")
    parser.add_argument("--user",     default=None,         help="your display name on the platform")
    parser.add_argument("--data-dir", default="experience", help="data directory path")
    args = parser.parse_args()

    from .ingest import ingest_file
    config = EngineConfig(data_dir=args.data_dir)

    print(f"[ingest] Reading {args.file}...")
    result = ingest_file(
        filepath    = args.file,
        platform    = args.platform,
        config      = config,
        user_handle = args.user,
        verbose     = True,
    )

    if result.errors:
        print("[ingest] Errors:")
        for e in result.errors:
            print(f"  x {e}")

    print(f"[ingest] Done. {result.total_ingested} entries added to your experience log.")
    print("[ingest] Run experience-reflect next to extract beliefs from this data.")


def cmd_chat():
    """Full chat loop — kept minimal here, use chat.py for the full experience."""
    parser = argparse.ArgumentParser(description="Experience-aware chat")
    parser.add_argument("--data-dir",   default="experience", help="data directory path")
    parser.add_argument("--model",      default="mistral",    help="Ollama model name")
    parser.add_argument("--no-context", action="store_true",  help="disable experience injection")
    args = parser.parse_args()

    from .reflection import format_belief_block
    from .synthesis  import format_cognitive_block
    from .core       import log_interaction
    from .llm        import call

    config = EngineConfig(data_dir=args.data_dir, model=args.model)

    SYSTEM = (
        "You are a senior advisor with deep knowledge of this user's cognitive patterns. "
        "Write in direct prose. No numbered lists. Name cognitive patterns by label. "
        "Identify where their specific wiring creates risk. Be direct and specific.\n\n"
    )

    print(f"\n{'═'*64}")
    print("  Experience Engine — chat")
    print(f"  Context: {'OFF' if args.no_context else 'ON'}  |  Ctrl+C to exit")
    print(f"{'═'*64}\n")

    history: list[tuple[str, str]] = []

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if not question:
            continue

        context = "" if args.no_context else (
            format_cognitive_block(config) + format_belief_block(config=config)
        )

        conv = ""
        if history:
            conv = "## Recent conversation\n" + "\n".join(
                f"User: {q}\nAssistant: {a}" for q, a in history[-4:]
            ) + "\n\n"

        prompt = SYSTEM + context + conv + f"User: {question}\nAssistant:"

        try:
            answer = call(prompt, temperature=0.7, config=config)
        except RuntimeError as e:
            print(f"\n{e}\n")
            continue

        print(f"\nAssistant: {answer}\n")
        entry = log_interaction(question, answer, config=config)
        history.append((question, answer))
        print(f"  [logged | conf: {entry['confidence']:.2f}]\n")
