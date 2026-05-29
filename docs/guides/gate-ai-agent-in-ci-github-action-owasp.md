---
layout: default
title: "How to gate an AI agent in CI with a free GitHub Action (OWASP-Agentic-aligned)"
description: "How to gate an AI agent in CI with a free GitHub Action (OWASP-Agentic-aligned) — free, deterministic, CI-native, OWASP-Agentic-aligned."
---

# How to gate an AI agent in CI with a free GitHub Action (OWASP-Agentic-aligned)

Tool-using agents regress silently — a model swap or prompt tweak can quietly break tool selection, leak context across sessions, or open a prompt-injection hole that no unit test will catch. The fix isn't more dashboards; it's a pass/fail CI gate that fails the build the moment a high-severity failure appears, the same way a failing unit test does.

## Why deterministic evaluation matters in CI

LLM-as-judge pipelines are probabilistic: the same agent output can score differently on two consecutive runs, which makes them unreliable as hard CI gates. A flaky gate is worse than no gate — teams start ignoring it. `agent-eval` takes a different approach: every test case has a deterministic expected outcome (tool called, tool NOT called, output contains/excludes a string, session boundary respected). The result is a reproducible pass/fail signal you can defend in a PR review or a compliance audit.

The cases are also mapped to the [OWASP Agentic AI Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/), so when a case fails you know whether you're looking at a tool-misuse regression (A2), a prompt-injection exposure (A1), or a privilege-escalation risk (A6) — not just "the eval score dropped 3 points."

## Zero-config smoke test first

Before wiring anything into CI, verify the runner works against your model:

```bash
pip install "agent-eval-runner[openai]"
export OPENAI_API_KEY=sk-...
agent-eval try --model openai:gpt-4o
```

This runs the bundled starter cases against the live model and prints a pass/fail summary. No config files, no adapter needed. It's a sanity check, not a gate — but it tells you immediately whether your environment is wired correctly.

## The GitHub Action workflow

Here's the complete workflow. Drop it into `.github/workflows/agent-eval.yml` verbatim:

```yaml
# .github/workflows/agent-eval.yml
name: agent-eval
on: [push, pull_request]
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e .
      - uses: weiseer/agent-eval-action@v1
        with:
          cases: ./cases
          adapter: my_pkg.evals:agent
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

A few things worth noting:

- **`cases: ./cases`** — points to your directory of YAML test cases. The free 5-case starter pack gives you a working `./cases` folder immediately. The full 28-case OWASP-Agentic pack covers every Top 10 category.
- **`adapter: my_pkg.evals:agent`** — a Python callable that wraps your agent. The action imports it, feeds each case's input, and compares the output against the deterministic assertion. You write the adapter once; it's just a function that takes a string and returns a string (or a structured response your cases expect).
- **`OPENAI_API_KEY`** — stored as a GitHub Actions secret, never in the repo. If your agent uses a different provider, you swap the secret; the eval framework is provider-agnostic.
- **Exit code semantics** — the action exits non-zero on any high-severity case failure, which means GitHub marks the check as failed and blocks the merge if you've set branch protection rules. Low-severity warnings are surfaced in the report but don't break the build.

## Running locally before pushing

```bash
agent-eval run --cases ./cases --adapter my_module:agent --report signoff.md
```

This produces `signoff.md` — a human-readable report you can attach to a release or compliance ticket. Same deterministic logic as the Action, same exit code semantics. If it passes locally it will pass in CI, because there's no LLM judge in the loop whose mood can change between runs.

## What the OWASP-Agentic alignment actually gives you

The 28-case pack isn't just a checklist. Each case is a concrete adversarial or regression scenario: a prompt that attempts to hijack tool selection, an input designed to bleed data across a session boundary, a request that should trigger a privilege check but might not. When the build fails on one of these, you get the OWASP category in the report, which maps directly to the risk your security team already tracks. That makes the gate defensible — "we run OWASP Agentic Top 10 checks on every PR" is a statement you can make to an auditor.

## The positioning in one sentence

This is a free, deterministic, CI-native pass/fail gate — not another observability platform, not a hosted LLM-as-judge service with per-token costs and non-reproducible scores. It's the `pytest` of agent safety: runs in your pipeline, fails the build, tells you exactly which OWASP category broke and why.

---

_Free 5-case starter: https://github.com/weiseer/ai-agent-qa-eval-pack-starter · GitHub Action: https://github.com/weiseer/agent-eval-action · full 28-case OWASP-Agentic pack: https://weiseer.gumroad.com/l/dcipxt_