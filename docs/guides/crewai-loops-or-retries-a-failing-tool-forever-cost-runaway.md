---
layout: default
title: "How to test when CrewAI loops or retries a failing tool forever (cost runaway)"
description: "Catch and test the failure mode where CrewAI loops or retries a failing tool forever (cost runaway) — a deterministic eval + one-command runner."
---

# How to test when CrewAI loops or retries a failing tool forever (cost runaway)

Infinite retry loops in CrewAI are one of the most expensive silent failures you can ship — the agent keeps calling a broken tool, accumulates tokens on every attempt, and your bill climbs while the task never completes.

## Why This Failure Is Silent and Dangerous

CrewAI agents are designed to be persistent. When a tool raises an exception or returns an error string, the agent's underlying LLM often interprets that as "try again with a slightly different input" rather than "give up." There's no built-in hard wall on retry count by default, and nothing in your logs screams "runaway" — you just see repeated tool calls until you hit a rate limit, a timeout, or your credit card does the work for you.

The failure is especially insidious because:

- **It looks like progress.** Each loop produces a new LLM call with slightly varied arguments, so traces look active.
- **It's environment-dependent.** A tool that works in dev (fast network, mock API) silently fails in staging (real API, rate limits), triggering the loop only in production.
- **CrewAI's `max_iter` default is 25.** That's 25 LLM round-trips before the agent gives up — and `max_iter` only caps the agent's reasoning steps, not individual tool call retries within a step.

## The Correct Way to Test for This

The strategy is to inject a tool that always fails, then assert the agent stops within a bounded number of attempts and surfaces a failure rather than looping silently.

```python
import pytest
from unittest.mock import MagicMock, patch
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# --- A tool that always fails ---
class AlwaysFailingToolInput(BaseModel):
    query: str = Field(description="Any query")

class AlwaysFailingTool(BaseTool):
    name: str = "always_failing_tool"
    description: str = "Fetches data from an external API"
    args_schema: type[BaseModel] = AlwaysFailingToolInput

    def _run(self, query: str) -> str:
        # Simulates a persistently broken external API
        raise RuntimeError("External API is down")

# --- Track how many times the tool is invoked ---
call_counter = {"count": 0}
original_run = AlwaysFailingTool._run

def counting_run(self, query: str) -> str:
    call_counter["count"] += 1
    return original_run(self, query)

def test_agent_does_not_loop_forever_on_failing_tool():
    call_counter["count"] = 0

    failing_tool = AlwaysFailingTool()

    # Patch _run to count invocations
    with patch.object(AlwaysFailingTool, "_run", counting_run):
        agent = Agent(
            role="Data Fetcher",
            goal="Fetch data using the available tool",
            backstory="You retrieve data from external APIs.",
            tools=[failing_tool],
            max_iter=5,          # Tighten the cap for test speed
            max_retry_limit=1,   # Limit per-tool retries
            verbose=False,
            llm="gpt-4o-mini",   # Use cheapest model in tests
        )

        task = Task(
            description="Use the always_failing_tool to fetch data about 'sales'.",
            expected_output="A summary of sales data.",
            agent=agent,
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=False)

        result = crew.kickoff()

    # The agent must stop — assert it didn't loop beyond max_iter
    assert call_counter["count"] <= agent.max_iter, (
        f"Tool was called {call_counter['count']} times — "
        f"exceeded max_iter={agent.max_iter}. Cost runaway detected."
    )

    # The result should acknowledge failure, not be empty or a hallucinated success
    result_text = str(result).lower()
    assert any(word in result_text for word in ["unable", "failed", "error", "could not", "apolog"]), (
        f"Agent returned a result that looks like success despite tool always failing: {result}"
    )
```

## What This Test Validates

1. **Bounded invocations.** `call_counter["count"] <= agent.max_iter` ensures the tool was not called in an unbounded loop. If CrewAI's retry logic changes in a future version and ignores `max_iter`, this test catches it immediately.

2. **Honest failure surfacing.** The second assertion checks that the agent's final output admits failure rather than hallucinating a successful result — a separate but equally dangerous failure mode.

3. **`max_retry_limit=1`.** Set this on the `Agent` constructor to limit how many times the agent re-attempts a tool call within a single reasoning step. Combined with `max_iter`, this is your two-layer cost guard.

## Practical Hardening Checklist

- Always set `max_iter` explicitly — don't rely on the default 25 in production agents.
- Set `max_retry_limit=1` or `2` for any agent calling external APIs.
- In CI, run this test against every tool your agents use, with a mock that returns errors, to catch regressions before they hit production billing.
- Log `tool_call_count` as a metric in your observability stack so you can alert on runaway patterns in production even when tests pass.

_Want this as a ready-to-run check across 28 OWASP-Agentic-aligned cases? `pip install "agent-eval-runner[openai]"` then `agent-eval try --model openai:gpt-4o` — free 5-case starter: https://github.com/weiseer/ai-agent-qa-eval-pack-starter · full pack: https://weiseer.gumroad.com/l/dcipxt_