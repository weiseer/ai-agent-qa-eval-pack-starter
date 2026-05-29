---
layout: default
title: "AI Agent QA Guides — test the silent failures of tool-using LLM agents"
description: "Deterministic eval guides for LangChain, OpenAI, Anthropic, CrewAI, LangGraph & RAG agents — OWASP Agentic Top 10 aligned."
---

# AI Agent QA Guides

Practical, framework-native guides for catching the *silent* failure modes of tool-using LLM agents — wrong tool selection, hallucinated tool results, prompt injection, excessive agency, cost runaway, memory poisoning. Each maps to the OWASP Top 10 for Agentic Applications and ends with a one-command check.

Gate them all in CI with the [agent-eval-runner](https://pypi.org/project/agent-eval-runner/) or the [GitHub Action](https://github.com/weiseer/agent-eval-action).

## Guides

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
