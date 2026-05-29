---
layout: default
title: "A free, deterministic alternative to hosted LLM-eval platforms for CI gating"
description: "A free, deterministic alternative to hosted LLM-eval platforms for CI gating — free, deterministic, CI-native, OWASP-Agentic-aligned."
---

# A free, deterministic alternative to hosted LLM-eval platforms for CI gating

Hosted LLM evaluation platforms solve a real problem — but if your primary need is a reproducible pass/fail gate in CI, they often bring more infrastructure than the job requires.

## The category trade-off

Hosted observability and eval platforms are genuinely powerful for production monitoring: they capture traces, aggregate metrics over time, and many use LLM-as-judge scoring to evaluate free-form outputs at scale. That's the right tool when you need a dashboard, a feedback loop across thousands of live requests, or qualitative grading of open-ended responses.

The trade-off is weight. You're adopting a hosted service, a pricing model, and — critically — a non-deterministic judge. When an LLM grades your agent's output, the same run can pass on Tuesday and fail on Wednesday. That's acceptable for exploratory analysis; it's a problem for a CI gate that engineers need to trust and defend in a pull request review.

A lightweight, deterministic, code-first eval runner occupies a different niche: **free, runs locally or in CI, produces the same result every time, and blocks the merge if the agent regresses.** No dashboard subscription, no judge model, no flakiness.

## What "deterministic" actually means here

Deterministic eval means the pass/fail decision is computed by pure logic — string matching, regex, JSON schema validation, structured assertion — not by asking a second LLM whether the first LLM did a good job. Given the same agent output and the same case definition, the result is identical across machines, across runs, across time. That makes it auditable: you can point to the exact assertion that failed, reproduce it in 30 seconds, and explain it to a non-ML stakeholder without invoking probability.

This maps cleanly onto the **OWASP Agentic Top 10** threat categories — prompt injection, excessive agency, insecure tool use, and so on — where the failure modes are structural and testable, not matters of opinion.

## Who this is for

- Teams shipping an agent feature who want a regression gate before it merges, not after it's live
- Engineers who've been burned by flaky LLM-as-judge scores blocking or unblocking PRs unpredictably
- Projects where the eval budget is zero and the observability platform budget is also zero
- Anyone who needs to show a compliance or security reviewer exactly which OWASP-aligned cases pass

If you need production tracing, latency histograms, or qualitative scoring of long-form outputs at scale, a hosted platform is still the right answer. This is for the CI gate problem specifically.

## Try it in two minutes

Install the runner and fire a quick smoke test against a live model:

```bash
pip install "agent-eval-runner[openai]"
export OPENAI_API_KEY=sk-...
agent-eval try --model openai:gpt-4o
```

This runs a small built-in case set and prints a pass/fail summary to stdout. No account, no config file, no network call to a third-party eval service.

## Drop it into CI

The GitHub Action wraps the same runner. Add this to your repo and every push gets a deterministic eval gate:

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

Your `cases/` directory holds the eval cases; `adapter` points to the Python callable that wraps your agent. The action exits non-zero on any failure, blocking the merge exactly like a failing unit test.

For a full local run that writes a sign-off report:

```bash
agent-eval run --cases ./cases --adapter my_module:agent --report signoff.md
```

The `signoff.md` artifact is useful for audit trails — a timestamped, human-readable record of which cases passed before a release.

## The case library matters as much as the runner

A deterministic runner is only as useful as the cases you feed it. The free 5-case starter pack covers the basics. The full 28-case pack is structured around the OWASP Agentic Top 10, giving you coverage across prompt injection resistance, tool-call boundary enforcement, data exfiltration paths, and excessive agency scenarios — the categories most likely to matter to a security review, not just a product demo.

Because every case is a structured file with explicit assertions, you can read them, modify them, and add your own without touching the runner internals. The eval layer stays in your repo, under your version control, reviewable in the same PR as the agent code it tests.

---

_Free 5-case starter: https://github.com/weiseer/ai-agent-qa-eval-pack-starter · GitHub Action: https://github.com/weiseer/agent-eval-action · full 28-case OWASP-Agentic pack: https://weiseer.gumroad.com/l/dcipxt_