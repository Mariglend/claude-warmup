#!/usr/bin/env python3
"""
claude-warmup — Cognitive warm-up for Claude Code sessions
===========================================================
Before starting a complex task, run a structured warm-up that:
  1. Maps the codebase architecture
  2. Identifies patterns, conventions, and key decisions
  3. Builds a rich context document injected into every subsequent session

This reduces mid-session incoherence because Claude starts with a dense,
structured understanding of the project instead of discovering it lazily
during the actual task.

USAGE:
    python warmup.py ./myproject
    python warmup.py ./myproject --task "refactor the auth module"
    python warmup.py ./myproject --depth deep --output context.md
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── ANSI ──────────────────────────────────────────────────────────────────────
C = "\033[0;36m"; G = "\033[0;32m"; Y = "\033[1;33m"
R = "\033[0;31m"; B = "\033[1m"; DIM = "\033[2m"; RESET = "\033[0m"

# ── Warm-up stages ────────────────────────────────────────────────────────────
# Each stage is a focused micro-task that builds one layer of understanding.
# Like a squat warm-up: empty bar → 60% → 80% → working weight.

STAGES = [
    {
        "id": "architecture",
        "name": "Architecture scan",
        "emoji": "🏗️",
        "prompt": """Analyze this project and produce a structured architecture summary.
Cover: main components and their responsibilities, directory structure logic,
entry points, core data flow, and any notable design patterns used.
Be concise. Use headers. Max 400 words."""
    },
    {
        "id": "conventions",
        "name": "Conventions & style",
        "emoji": "📐",
        "prompt": """Analyze this project's coding conventions.
Cover: naming patterns (variables, functions, files), error handling style,
how imports are organized, comment style, any linting/formatting config found.
Be concise. Max 300 words."""
    },
    {
        "id": "dependencies",
        "name": "Dependencies & interfaces",
        "emoji": "🔗",
        "prompt": """Analyze this project's external dependencies and internal interfaces.
Cover: key libraries and why they're used, main internal APIs/interfaces between modules,
any external services or configs required.
Be concise. Max 300 words."""
    },
    {
        "id": "risks",
        "name": "Fragile zones",
        "emoji": "⚠️",
        "prompt": """Identify the most fragile or complex parts of this codebase.
Cover: files/functions with high complexity, known TODOs or FIXMEs,
areas with missing tests, any obvious tech debt.
Be concise and specific. Max 300 words."""
    },
    {
        "id": "task_context",
        "name": "Task alignment",
        "emoji": "🎯",
        "prompt": None,  # built dynamically if --task is provided
    },
]

FAST_STAGES = ["architecture", "conventions"]  # used with --depth fast


def run_claude(prompt: str, model: str, project_path: Optional[str] = None,
               timeout: int = 120) -> tuple[str, int]:
    cmd = ["claude", "--print", "--model", model]
    if project_path:
        full_prompt = f"Project path: {project_path}\n\n{prompt}"
    else:
        full_prompt = prompt
    try:
        result = subprocess.run(
            cmd, input=full_prompt, capture_output=True, text=True, timeout=timeout
        )
        return (result.stdout + result.stderr).strip(), result.returncode
    except subprocess.TimeoutExpired:
        return f"ERROR: timeout after {timeout}s", 1
    except FileNotFoundError:
        return "ERROR: 'claude' not found. Install Claude Code CLI.", 127


def run_warmup(project_path: str, task: Optional[str], depth: str,
               model: str, output_path: Path) -> dict:

    project = Path(project_path).resolve()
    if not project.exists():
        print(f"{R}Error: path '{project_path}' does not exist.{RESET}")
        sys.exit(1)

    # Select stages based on depth
    if depth == "fast":
        active_ids = FAST_STAGES
    elif depth == "deep":
        active_ids = [s["id"] for s in STAGES]
    else:  # normal
        active_ids = ["architecture", "conventions", "dependencies", "risks"]

    # Add task alignment only if --task provided
    if task and "task_context" not in active_ids:
        active_ids.append("task_context")

    active_stages = [s for s in STAGES if s["id"] in active_ids]

    print(f"\n{B}{C}╔══════════════════════════════════════════╗")
    print(f"║        claude-warmup  🧠  v1.0.0         ║")
    print(f"╚══════════════════════════════════════════╝{RESET}\n")
    print(f"{B}Project:{RESET} {project}")
    if task:
        print(f"{B}Task:{RESET}    {task}")
    print(f"{B}Depth:{RESET}   {depth} ({len(active_stages)} stages)")
    print(f"{B}Model:{RESET}   {model}")
    print(f"{DIM}{'─' * 46}{RESET}\n")

    results = {}
    start_all = time.time()

    for i, stage in enumerate(active_stages):
        # Build prompt for task_context stage dynamically
        if stage["id"] == "task_context":
            if not task:
                continue
            prompt = f"""Given this task: "{task}"
Analyze the project and identify:
1. Which files/modules are most relevant to this task
2. What existing code can be reused
3. What are the main risks or complications for this specific task
4. Suggested approach in 3-5 steps
Be specific and concise. Max 400 words."""
        else:
            prompt = stage["prompt"]

        print(f"  {stage['emoji']}  {B}Stage {i+1}/{len(active_stages)}{RESET}: {stage['name']}...", end=" ", flush=True)
        t0 = time.time()
        output, code = run_claude(prompt, model, str(project))
        elapsed = time.time() - t0

        if code == 0:
            print(f"{G}✓{RESET} {DIM}({elapsed:.1f}s){RESET}")
            results[stage["id"]] = output
        else:
            print(f"{Y}⚠ partial{RESET} {DIM}({elapsed:.1f}s){RESET}")
            results[stage["id"]] = output  # keep even if partial

    total_time = time.time() - start_all

    # ── Build context document ────────────────────────────────────────────────
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    doc_lines = [
        f"# Claude Code — Project Context",
        f"",
        f"**Generated:** {ts}  ",
        f"**Project:** `{project}`  ",
        f"**Warmup depth:** {depth}  ",
    ]
    if task:
        doc_lines += [f"**Active task:** {task}  "]

    doc_lines += [
        f"",
        f"---",
        f"",
        f"> This document was generated by `claude-warmup` as a cognitive primer.",
        f"> Inject it at the start of any Claude Code session on this project",
        f"> to reduce context discovery overhead and improve coherence.",
        f"",
        f"---",
        f"",
    ]

    stage_titles = {
        "architecture": "## 🏗️ Architecture",
        "conventions": "## 📐 Conventions & Style",
        "dependencies": "## 🔗 Dependencies & Interfaces",
        "risks": "## ⚠️ Fragile Zones",
        "task_context": "## 🎯 Task Alignment",
    }

    for stage_id, content in results.items():
        title = stage_titles.get(stage_id, f"## {stage_id}")
        doc_lines += [title, "", content, ""]

    doc_lines += [
        "---",
        "",
        "## 🚀 How to use this context",
        "",
        "Start your Claude Code session with:",
        "",
        "```",
        "Read the file context.md carefully before doing anything else.",
        "This is the project context you need to work effectively.",
        "```",
        "",
        f"*Generated in {total_time:.1f}s*",
    ]

    context_doc = "\n".join(doc_lines)
    output_path.write_text(context_doc, encoding="utf-8")

    return {
        "stages_completed": len(results),
        "total_seconds": round(total_time, 1),
        "output_file": str(output_path),
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Cognitive warm-up for Claude Code — build a rich context document before complex tasks"
    )
    parser.add_argument("project", help="Path to the project directory")
    parser.add_argument("--task", "-t", metavar="DESCRIPTION",
                        help="The specific task you're about to work on (enables task alignment stage)")
    parser.add_argument("--depth", choices=["fast", "normal", "deep"], default="normal",
                        help="fast=2 stages, normal=4 stages, deep=5 stages (default: normal)")
    parser.add_argument("--output", "-o", default="context.md",
                        help="Output file for the context document (default: context.md)")
    parser.add_argument("--model", default="claude-sonnet-4-20250514",
                        help="Claude model to use")
    args = parser.parse_args()

    output_path = Path(args.output)

    summary = run_warmup(
        project_path=args.project,
        task=args.task,
        depth=args.depth,
        model=args.model,
        output_path=output_path,
    )

    print(f"\n{DIM}{'─' * 46}{RESET}")
    print(f"{G}{B}✓ Warm-up complete{RESET} — {summary['stages_completed']} stages in {summary['total_seconds']}s")
    print(f"\n{B}Context document:{RESET} {output_path.resolve()}")
    print(f"\n{B}Next step — start your Claude Code session with:{RESET}")
    print(f"{DIM}  Read {output_path} carefully before doing anything else.")
    print(f"  This is the project context you need to work effectively.{RESET}\n")


if __name__ == "__main__":
    main()
