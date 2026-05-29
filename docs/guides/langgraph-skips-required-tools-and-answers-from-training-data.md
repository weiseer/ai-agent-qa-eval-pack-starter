---
layout: default
title: "How to test when LangGraph skips required tools and answers from training data"
description: "Catch and test the failure mode where LangGraph skips required tools and answers from training data — a deterministic eval + one-command runner."
---

# How to test when LangGraph skips required tools and answers from training data

LangGraph agents can silently hallucinate answers from training data instead of calling the tools you wired up — and the graph still returns `SUCCESS`, so your normal integration tests never catch it.

## Why This Failure Is Dangerous

When a LangGraph agent skips a required tool call, the graph completes normally. There's no exception, no error state, no missing key in the output dict. The agent just routes straight to `END` using memorized knowledge instead of live data. In production this means stale prices, wrong inventory counts, fabricated API responses — all delivered with full confidence. The only way to catch it is to explicitly assert that specific tools were invoked.

## How LangGraph Tool Calls Work (and Where the Gap Is)

LangGraph tracks tool invocations through `AIMessage.tool_calls` on the messages in state. When the LLM decides to call a tool, it emits an `AIMessage` with a populated `tool_calls` list. When it skips the tool and answers directly, that list is empty. Your test needs to inspect the message history and verify the right tool names appear.

## A Minimal, Runnable Test

This example builds a small LangGraph agent with a required `get_stock_price` tool, runs it, and asserts the tool was actually called — not silently bypassed.

```python
import pytest
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent


# Define the tool the agent is required to use
@tool
def get_stock_price(ticker: str) -> str:
    """Get the current stock price for a ticker symbol."""
    # In real tests, mock this or use a fixture
    return f"${ticker}: 142.50"


def build_agent():
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    return create_react_agent(llm, tools=[get_stock_price])


def extract_tool_calls(messages: list) -> list[str]:
    """Return a flat list of tool names called during the run."""
    called = []
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                called.append(tc["name"])
    return called


def test_agent_calls_get_stock_price_not_training_data():
    agent = build_agent()

    result = agent.invoke({
        "messages": [HumanMessage(content="What is the current price of AAPL?")]
    })

    messages = result["messages"]
    called_tools = extract_tool_calls(messages)

    # Core assertion: the required tool must appear in the trace
    assert "get_stock_price" in called_tools, (
        f"Agent answered from training data instead of calling get_stock_price. "
        f"Tools actually called: {called_tools}"
    )

    # Secondary: a ToolMessage must exist (confirms tool actually executed)
    tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
    assert len(tool_messages) >= 1, "No ToolMessage found — tool was never executed"

    # Optional: final answer should reference the mocked price
    final_answer = messages[-1].content
    assert "142.50" in final_answer, (
        f"Final answer doesn't reflect tool output, got: {final_answer}"
    )


def test_agent_does_not_skip_tool_for_known_ticker():
    """Regression test: even 'well-known' tickers must go through the tool."""
    agent = build_agent()

    # GPT-4o knows MSFT's approximate price from training — this is the risky case
    result = agent.invoke({
        "messages": [HumanMessage(content="What is Microsoft's stock price? Ticker is MSFT.")]
    })

    called_tools = extract_tool_calls(result["messages"])
    assert "get_stock_price" in called_tools, (
        "Agent used training data for a well-known ticker instead of calling the tool. "
        f"Called: {called_tools}"
    )
```

## Run It

```bash
pip install langgraph langchain-openai pytest
OPENAI_API_KEY=sk-... pytest test_tool_skip.py -v
```

## What to Watch For

**The `test_agent_does_not_skip_tool_for_known_ticker` test is the important one.** LLMs are most likely to skip tools when they already "know" the answer — popular stock tickers, capital cities, common unit conversions. Your tool-call assertions need to cover exactly those cases, not just obscure inputs where the model has no choice.

**Strengthen the system prompt.** If tests fail intermittently, add explicit instruction: `"You MUST call get_stock_price for any price question. Never use training data for prices."` Then re-run the test suite to confirm the prompt change actually holds.

**Mock the tool in CI.** Replace the tool body with a deterministic fixture value so your tests don't depend on live APIs or real LLM costs. The assertion logic stays identical — you're testing routing behavior, not the tool's output.

**Check `tool_calls` before `ToolMessage`.** An `AIMessage` with `tool_calls` populated but no corresponding `ToolMessage` means the graph routed incorrectly after the LLM decision. Both assertions together catch different failure modes.

_Want this as a ready-to-run check across 28 OWASP-Agentic-aligned cases? `pip install "agent-eval-runner[openai]"` then `agent-eval try --model openai:gpt-4o` — free 5-case starter: https://github.com/weiseer/ai-agent-qa-eval-pack-starter · full pack: https://weiseer.gumroad.com/l/dcipxt_