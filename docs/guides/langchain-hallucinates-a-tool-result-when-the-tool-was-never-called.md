---
layout: default
title: "How to test when LangChain hallucinates a tool result when the tool was never called"
description: "Catch and test the failure mode where LangChain hallucinates a tool result when the tool was never called — a deterministic eval + one-command runner."
---

# How to test when LangChain hallucinates a tool result when the tool was never called

Hallucinated tool results are one of the quietest failure modes in LangChain agents: the model fabricates a plausible-looking tool output, the chain continues as if the tool ran, and your application returns confident nonsense with zero exceptions raised and no stack trace to chase.

## Why this failure is silent

LangChain's `AgentExecutor` trusts the LLM's output. If the model emits a final answer that incorporates a "result" it invented — without ever emitting a valid `Action`/`Action Input` pair that triggers your tool — the executor simply returns that answer. There is no built-in assertion that every fact in the final answer was grounded by an actual tool invocation. Your logs show a clean run. Your users get a lie.

The failure is especially dangerous with tools that return sensitive or authoritative data: stock prices, database lookups, API calls. The model has seen enough training data to fabricate convincing outputs for all of them.

## How to detect it: instrument the tool

The correct approach is to wrap your tool so it records whether it was actually called, then assert on that record after the agent runs. Here is a minimal, runnable example using LangChain's real API.

```python
import pytest
from unittest.mock import MagicMock
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain import hub

# --- 1. Define a tool with a call-tracking side effect ---

call_log = []

@tool
def get_account_balance(account_id: str) -> str:
    """Returns the current balance for the given account ID."""
    call_log.append(account_id)          # record every real invocation
    return f"Balance for {account_id}: $1,234.56"

# --- 2. Build the agent ---

def make_agent():
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm, [get_account_balance], prompt)
    return AgentExecutor(agent=agent, tools=[get_account_balance], verbose=True)

# --- 3. The test ---

def test_agent_actually_calls_tool_before_reporting_balance():
    call_log.clear()

    executor = make_agent()
    result = executor.invoke({
        "input": "What is the current balance for account ACC-9921?"
    })

    # The agent must have called the tool at least once
    assert len(call_log) > 0, (
        "Agent returned a balance without ever calling get_account_balance. "
        f"Final answer was: {result['output']}"
    )

    # The tool must have been called with the right account
    assert "ACC-9921" in call_log, (
        f"Tool was called, but not with the expected account ID. "
        f"Actual calls: {call_log}"
    )

    # The final answer must reference the real return value, not a fabrication
    assert "1,234.56" in result["output"], (
        "Final answer does not contain the value the tool actually returned. "
        "Possible hallucination in the answer synthesis step."
    )
```

Run it with `pytest test_tool_hallucination.py -s` (the `-s` flag lets you see the agent's verbose trace alongside the assertion results).

## What each assertion catches

| Assertion | Failure it catches |
|---|---|
| `len(call_log) > 0` | Pure hallucination — tool never invoked at all |
| `"ACC-9921" in call_log` | Tool called with wrong/fabricated arguments |
| `"1,234.56" in result["output"]` | Tool ran but answer was synthesized from model memory, not tool output |

The third check matters because a model can call your tool correctly and then *ignore* its return value, substituting a hallucinated figure in the final answer. All three assertions together form a complete grounding check.

## Hardening the pattern

For tools that should never be called more than once per query, add `assert len(call_log) == 1`. For multi-tool chains, maintain a dict keyed by tool name. If you want to test the *absence* of a tool call (e.g., the agent should answer from context and must not hit an expensive API), assert `len(call_log) == 0` after the run.

You can also replace the real LLM with a `FakeListLLM` that emits a pre-scripted hallucinated answer to make the test deterministic and free:

```python
from langchain_community.llms.fake import FakeListLLM

def test_hallucination_detected_with_fake_llm():
    call_log.clear()
    # Simulate a model that skips the tool and goes straight to Final Answer
    fake_llm = FakeListLLM(responses=[
        "Final Answer: The balance for ACC-9921 is $99,999.00"
    ])
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(fake_llm, [get_account_balance], prompt)
    executor = AgentExecutor(agent=agent, tools=[get_account_balance])

    result = executor.invoke({"input": "Balance for ACC-9921?"})

    assert len(call_log) == 0   # confirms the fake skipped the tool
    # Now your production guard should have caught this — assert it did:
    assert "1,234.56" not in result["output"], "Real value leaked in — check your grounding logic"
```

This gives you a repeatable, zero-cost regression test you can run in CI without an API key.

_Want this as a ready-to-run check across 28 OWASP-Agentic-aligned cases? `pip install "agent-eval-runner[openai]"` then `agent-eval try --model openai:gpt-4o` — free 5-case starter: https://github.com/weiseer/ai-agent-qa-eval-pack-starter · full pack: https://weiseer.gumroad.com/l/dcipxt_