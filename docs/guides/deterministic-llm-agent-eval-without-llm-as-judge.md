---
layout: default
title: "Deterministic LLM agent evaluation without LLM-as-judge"
description: "Deterministic LLM agent evaluation without LLM-as-judge — free, deterministic, CI-native, OWASP-Agentic-aligned."
---

# Deterministic LLM agent evaluation without LLM-as-judge

Shipping an LLM agent to production requires a quality gate you can defend — and an LLM-as-judge gate is surprisingly hard to defend once you look closely at how it behaves.

## The reproducibility problem with LLM-as-judge

When you ask a language model to score another language model's output, you introduce a second source of non-determinism. Run the same evaluation twice and the judge may return different verdicts. Temperature, sampling, and the judge model's own context window all contribute. In practice this means a test that passes on Monday's CI run can fail on Wednesday's without any change to your agent — or, more dangerously, a real failure can slip through because the judge happened to be lenient on that particular run.

There's also a well-documented positional and verbosity bias: LLM judges tend to favor longer, more confident-sounding responses regardless of correctness, and they often rate outputs from the same model family more favorably. For a production sign-off gate, "the judge liked it" is not an auditable criterion. A compliance reviewer, a security team, or a post-incident retrospective will ask what the test actually checked — and "we asked GPT-4 if it seemed okay" is a weak answer.

## What deterministic evaluation looks like

The alternative is to express your pass/fail criteria as assertions that produce the same result every time, on every machine, with no API call to a judge model:

- **Required keywords** — the response must contain specific strings (e.g., a disclaimer, a structured field, a required citation).
- **Forbidden keywords** — the response must not contain strings that indicate a failure mode (e.g., a competitor name in a brand-safety case, a PII pattern, a known hallucination marker).
- **Regex patterns** — structured output validation, phone/email redaction checks, format conformance.
- **Refusal detection** — the agent must (or must not) decline a request; checked against a fixed refusal-phrase list, not a judge's opinion.
- **Tool-call trace invariants** — the agent called the right tools in the right order, did not call a forbidden tool, or did not exceed a call-count budget.

These assertions are boring in the best possible way. Given the same agent output, they return the same result every single time. That makes your CI gate reproducible, your sign-off auditable, and your regression history meaningful — a red build means something broke, not that the judge was in a bad mood.

This approach also maps directly onto the [OWASP Agentic Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/) risk categories. Prompt injection resistance, excessive agency, and sensitive data exposure all have concrete, checkable signatures — you don't need a judge to tell you whether your agent leaked a secret; you check whether the forbidden pattern appears in the output.

## Trying it in one command

The `agent-eval-runner` package lets you run deterministic cases against any agent callable. To see it work immediately against a hosted model:

```bash
pip install "agent-eval-runner[openai]"
export OPENAI_API_KEY=sk-...
agent-eval try --model openai:gpt-4o
```

This runs the bundled starter cases and prints a pass/fail table — no judge model, no scoring rubric, just assertions evaluated against real outputs.

## Running against your own agent

Point the runner at your own case directory and adapter module:

```bash
agent-eval run --cases ./cases --adapter my_module:agent --report signoff.md
```

The `--adapter` flag takes a Python import path to a callable that accepts a prompt string and returns a response string (plus an optional tool-call trace). The `--report` flag writes a Markdown sign-off document you can attach to a PR or a release ticket. Every case either passes or fails; there is no "score of 7.2 out of 10."

## Putting it in CI

The GitHub Action wraps the same runner so the gate runs on every push and pull request:

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

The action exits non-zero on any case failure, blocking the merge. Because the assertions are deterministic, a green run is a green run — not a probabilistic estimate that the agent is probably fine.

## When you actually need an LLM judge

Deterministic assertions don't cover everything. Open-ended summarization quality, tone, and nuanced instruction-following genuinely require semantic judgment. The practical answer is to use deterministic gates for everything that *can* be checked deterministically — safety, format, tool-call invariants, refusal behavior — and reserve LLM-as-judge for the narrow slice of cases where no deterministic criterion exists. That way your CI gate is defensible, and your judge evaluations are scoped to where they add real value rather than substituting for rigor.

---

_Free 5-case starter: https://github.com/weiseer/ai-agent-qa-eval-pack-starter · GitHub Action: https://github.com/weiseer/agent-eval-action · full 28-case OWASP-Agentic pack: https://weiseer.gumroad.com/l/dcipxt_