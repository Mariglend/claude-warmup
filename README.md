# claude-warmup 🧠

**Cognitive warm-up for Claude Code sessions** — build a rich context document before tackling complex tasks to reduce mid-session incoherence and context discovery overhead.

---

## The Problem

When you drop Claude Code into a complex codebase and immediately ask it to do something hard, it spends the first part of the session *discovering* the project — architecture, conventions, which files matter — while simultaneously trying to solve your problem. This leads to:

- Inconsistent style (it didn't fully map conventions before writing)
- Missed dependencies (it didn't know module X existed)
- Incoherent decisions halfway through (context window fills up with discovery noise)

## The Insight

In sports, you don't squat your max without warming up. The warm-up doesn't make your muscles stronger permanently — it **primes the system** with the right activation state before the hard work begins.

The same principle applies here: a structured warm-up pass over the codebase, before the actual task, builds a dense context document that Claude can use as a primer. Instead of discovering the project lazily mid-task, it starts with a complete picture.

## How It Works

`claude-warmup` runs a series of small, focused analysis tasks on your project:

```
Stage 1 — Architecture scan       🏗️  What is this project and how is it structured?
Stage 2 — Conventions & style     📐  How is code written here?
Stage 3 — Dependencies            🔗  What does it depend on, what are the interfaces?
Stage 4 — Fragile zones           ⚠️  Where are the risky / complex parts?
Stage 5 — Task alignment          🎯  (optional) What's relevant to MY specific task?
```

Each stage is a short, isolated Claude session. The outputs are synthesized into a single `context.md` file that you inject at the start of your working session.

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/claude-warmup.git
cd claude-warmup
```

Requires: [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code), Python 3.8+

---

## Usage

### Basic warm-up
```bash
python warmup.py ./myproject
```

### With a specific task (recommended)
```bash
python warmup.py ./myproject --task "refactor the authentication module"
```
This activates the **Task Alignment** stage, which tells Claude exactly which files and risks are relevant to *your* task before you start.

### Depth control
```bash
python warmup.py ./myproject --depth fast    # 2 stages (~1 min)  — quick orientation
python warmup.py ./myproject --depth normal  # 4 stages (~3 min)  — default
python warmup.py ./myproject --depth deep    # 5 stages (~4 min)  — before big tasks
```

### Custom output file
```bash
python warmup.py ./myproject --output ./docs/session_context.md
```

### All options
```
positional:
  project             Path to the project directory

options:
  --task DESCRIPTION  The specific task you're about to work on
  --depth DEPTH       fast | normal | deep  (default: normal)
  --output FILE       Output path for context document (default: context.md)
  --model MODEL       Claude model to use
```

---

## The workflow

```bash
# 1. Run warm-up before starting work
python warmup.py ./myproject --task "add rate limiting to the API" --depth deep

# Output:
#   🏗️  Stage 1/5: Architecture scan...      ✓ (8.2s)
#   📐  Stage 2/5: Conventions & style...    ✓ (6.1s)
#   🔗  Stage 3/5: Dependencies...           ✓ (7.4s)
#   ⚠️   Stage 4/5: Fragile zones...          ✓ (8.9s)
#   🎯  Stage 5/5: Task alignment...         ✓ (9.1s)
#
#   ✓ Warm-up complete — 5 stages in 39.7s
#   Context document: /path/to/myproject/context.md

# 2. Start Claude Code, inject the context first
claude
> Read context.md carefully before doing anything else.
> This is the project context you need to work effectively.
> Now: add rate limiting to the API

# Claude starts the real task already knowing the full picture.
```

---

## Output: context.md

The generated document looks like this:

```markdown
# Claude Code — Project Context

**Generated:** 2026-05-07 14:32
**Project:** `/path/to/myproject`
**Active task:** add rate limiting to the API

---

## 🏗️ Architecture
[structured analysis of project components and data flow]

## 📐 Conventions & Style
[naming patterns, error handling, import style]

## 🔗 Dependencies & Interfaces
[key libraries, internal module boundaries]

## ⚠️ Fragile Zones
[complex areas, TODOs, missing tests]

## 🎯 Task Alignment
[files relevant to the task, risks, suggested approach]
```

---

## Why this works

The core mechanic is **front-loading context discovery** into short, isolated sessions before the main session begins. Benefits:

- Each warm-up stage has a small, focused context window — no degradation
- The synthesized document fits in ~1000 tokens, so injecting it costs little
- Claude starts the working session with a complete mental model instead of building one mid-task
- Conventions are explicit from the start, so generated code is consistent throughout

---

## Pair with

- [claude-swarm](https://github.com/YOUR_USERNAME/claude-swarm) — run warmup first, then distribute subtasks to parallel workers, each with the context injected
- [claude-resume](https://github.com/YOUR_USERNAME/claude-resume) — auto-resume on rate limit

---

## License

MIT
