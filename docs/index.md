---
layout: default
title: "Deterministic, CI-native eval for tool-using LLM agents (no LLM-as-judge)"
description: "Free, deterministic, OWASP-Agentic-aligned eval for tool-using LLM agents. A reproducible pass/fail CI gate — not another observability platform."
---

# Deterministic agent eval that gates CI — no LLM-as-judge

A **free**, **deterministic** eval pack + runner for tool-using LLM agents. The pass/fail is computed by pure logic (keywords, regex, refusal detection, tool-call trace invariants) — **not** by asking a second LLM. So the gate is **reproducible and defensible** in a PR review, **OWASP Agentic Top 10 aligned**, and drops into CI in one line. It's a pass/fail gate, not another observability platform.

```bash
pip install "agent-eval-runner[openai]"
agent-eval try --model openai:gpt-4o
```

Runner on [PyPI](https://pypi.org/project/agent-eval-runner/) · [GitHub Action](https://github.com/weiseer/agent-eval-action) · [free starter repo]() · [full 28-case pack](https://weiseer.gumroad.com/l/dcipxt)

## Start here

- [Deterministic LLM agent evaluation without LLM-as-judge](guides/deterministic-llm-agent-eval-without-llm-as-judge.html)
- [How to gate an AI agent in CI with a free GitHub Action (OWASP-Agentic-aligned)](guides/gate-ai-agent-in-ci-github-action-owasp.html)
- [A free, deterministic alternative to hosted LLM-eval platforms for CI gating](guides/free-deterministic-alternative-hosted-llm-eval-ci.html)

## More guides — failure modes by framework

- [How to test when a custom agent loop fails OWASP Agentic Top 10 memory & data poisoning](guides/a-custom-agent-loop-fails-owasp-agentic-top-10-memory-data-poisoning.html)
- [How to test when an AI agent should refuse but complies under a justification frame](guides/an-ai-agent-should-refuse-but-complies-under-a-justification-frame.html)
- [How to test when Anthropic tool use ignores a tool error and fabricates an answer](guides/anthropic-tool-use-ignores-a-tool-error-and-fabricates-an-answer.html)
- [How to test when Anthropic tool use takes an unrequested high-impact action (excessive agency)](guides/anthropic-tool-use-takes-an-unrequested-high-impact-action-excessive-a.html)
- [How to test when a RAG agent treats adversarial text in retrieved context as instructions](guides/a-rag-agent-treats-adversarial-text-in-retrieved-context-as-instructio.html)
- [How to test when a tool-using agent uses a high-privilege tool when a read-only tool would do](guides/a-tool-using-agent-uses-a-high-privilege-tool-when-a-read-only-tool-wo.html)
- [How to test when AutoGen is hijacked by a prompt injection inside a retrieved document](guides/autogen-is-hijacked-by-a-prompt-injection-inside-a-retrieved-document.html)
- [How to test when CrewAI lets one agent's output poison the next agent (cascading failure)](guides/crewai-lets-one-agent-s-output-poison-the-next-agent-cascading-failure.html)
- [How to test when CrewAI loops or retries a failing tool forever (cost runaway)](guides/crewai-loops-or-retries-a-failing-tool-forever-cost-runaway.html)
- [How to test when LangChain calls the wrong tool instead of the right one](guides/langchain-calls-the-wrong-tool-instead-of-the-right-one.html)
- [How to test when LangChain hallucinates a tool result when the tool was never called](guides/langchain-hallucinates-a-tool-result-when-the-tool-was-never-called.html)
- [How to test when LangGraph acts on poisoned memory from an earlier step](guides/langgraph-acts-on-poisoned-memory-from-an-earlier-step.html)
- [How to test when LangGraph skips required tools and answers from training data](guides/langgraph-skips-required-tools-and-answers-from-training-data.html)
- [How to test when OpenAI function calling gets prompt-injected by content inside a function result](guides/openai-function-calling-gets-prompt-injected-by-content-inside-a-funct.html)
- [How to test when OpenAI function calling passes malformed or wrong arguments to a function](guides/openai-function-calling-passes-malformed-or-wrong-arguments-to-a-funct.html)
