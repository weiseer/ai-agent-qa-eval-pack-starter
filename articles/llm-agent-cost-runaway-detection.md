# Catching Cost Runaway in Tool-Using LLM Agents Before Your Bill Explodes

You deploy a tool-using agent on Friday. By Monday morning you have a $3,000 surprise on your OpenAI invoice. The agent wasn't broken—it was *correct*. It just called the search tool 47 times per user query instead of 4.

This is the failure mode that's underappreciated in practice: agents that produce right answers via catastrophically inefficient paths.

---

## Why Tool-Using Agents Bleed Money

LLMs in agentic loops have no intrinsic cost awareness. Each tool call is another round-trip: tokens in, tokens out, sometimes an external API charge on top. Three patterns cause most runaway bills:

**Redundant tool calls** — the agent fetches the same data twice (or twelve times) because it doesn't track what it already retrieved. Common in ReAct loops where observations don't get surfaced clearly back into context.

**Missing iteration caps** — no hard limit on how many steps the loop can take. An ambiguous query can spin until the context window fills and the model errors out.

**No cost budget enforcement** — the agent has a soft "try to be efficient" prompt instruction but nothing that actually stops execution when a dollar threshold is crossed.

---

## Reproducing the Problem in Code

Here's a minimal LangChain-style agent with a deliberately leaky tool loop:

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain import hub

@tool
def search_database(query: str) -> str:
    """Search the product database."""
    return f"Results for: {query}"

@tool
def get_product_details(product_id: str) -> str:
    """Get details for a specific product."""
    return f"Details for product {product_id}"

llm = ChatOpenAI(model="gpt-4o", temperature=0)
prompt = hub.pull("hwchase17/react")
tools = [search_database, get_product_details]
agent = create_react_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, max_iterations=50)  # 50 is too high
```

The `max_iterations=50` is the first problem. The second: nothing deduplicates tool calls before they fire.

---

## A Deterministic Test for Cost Efficiency

The fix isn't just lowering `max_iterations`. You need a *test* that catches regressions. Use LangChain's `get_openai_callback()` context manager to capture real token counts, and keep call tracking local to each invocation to avoid shared-state bugs:

```python
import pytest
from collections import Counter
from langchain_community.callbacks import get_openai_callback

MAX_TOOL_CALLS = 6
MAX_DUPLICATE_RATIO = 0.15
COST_BUDGET_USD = 0.05  # per query

def run_agent_with_telemetry(query: str) -> dict:
    call_log = []  # local per invocation — no shared mutable state

    original_search = search_database.func
    original_details = get_product_details.func

    def tracked_search(q):
        call_log.append({"tool": "search_database", "key": q})
        return original_search(q)

    def tracked_details(pid):
        call_log.append({"tool": "get_product_details", "key": pid})
        return original_details(pid)

    with get_openai_callback() as cb:
        result = executor.invoke({"input": query})

    # gpt-4o pricing: input $2.50/1M tokens, output $10.00/1M tokens
    estimated_cost = (cb.prompt_tokens / 1_000_000 * 2.50) + \
                     (cb.completion_tokens / 1_000_000 * 10.00)

    return {
        "output": result["output"],
        "call_log": call_log,
        "estimated_cost": estimated_cost,
    }

@pytest.mark.parametrize("query", [
    "Find all laptops under $800 and get details for the top 3",
    "What products are on sale this week?",
    "Compare product A123 and B456",
])
def test_tool_call_efficiency(query):
    telemetry = run_agent_with_telemetry(query)
    calls = telemetry["call_log"]

    assert len(calls) <= MAX_TOOL_CALLS, (
        f"Too many tool calls ({len(calls)}) for: '{query}'"
    )

    signatures = [f"{c['tool']}:{c['key']}" for c in calls]
    counts = Counter(signatures)
    duplicates = sum(v - 1 for v in counts.values() if v > 1)
    dup_ratio = duplicates / len(calls) if calls else 0

    assert dup_ratio <= MAX_DUPLICATE_RATIO, (
        f"Duplicate ratio {dup_ratio:.0%} exceeds threshold. "
        f"Duplicates: {[k for k, v in counts.items() if v > 1]}"
    )

    assert telemetry["estimated_cost"] <= COST_BUDGET_USD, (
        f"Estimated cost ${telemetry['estimated_cost']:.4f} exceeds "
        f"budget ${COST_BUDGET_USD} for: '{query}'"
    )
```

Run this in CI on every prompt or system-prompt change. It will catch the Friday-deploy problem before Monday.

---

## Fixing the Agent Side

Once the test is red, here are the actual fixes:

**Deduplicate at the implementation level** — cache results by exact call signature inside the tool's underlying function:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def _search_database_impl(query: str) -> str:
    # real implementation here
    return f"Results for: {query}"

@tool
def search_database(query: str) -> str:
    """Search the product database."""
    return _search_database_impl(query)
```

This catches exact string duplicates. Semantic duplicates ("cheap laptops" vs "laptops under $800") require embedding-based dedup or stricter prompt design.

**Lower and enforce iteration limits:**

```python
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    max_iterations=8,
    max_execution_time=30.0,
    early_stopping_method="generate",
)
```

**Add a tool budget to the system prompt** (belt *and* suspenders):

```
You have a budget of 6 tool calls maximum per user query.
Before calling any tool, check if you already have the information
in your previous observations. Do not repeat identical calls.
```

These three changes together — caching, hard iteration caps, and prompt-level budget awareness — eliminate the majority of runaway cost scenarios in practice.

---

## What the Test Actually Catches

The three assertions in `test_tool_call_efficiency` map directly to the three failure modes:

| Assertion | Failure mode caught |
|---|---|
| `len(calls) <= MAX_TOOL_CALLS` | Unbounded loops / missing iteration cap |
| `dup_ratio <= MAX_DUPLICATE_RATIO` | Redundant fetches of identical data |
| `estimated_cost <= COST_BUDGET_USD` | Total spend exceeding acceptable threshold |

The cost assertion is the most important one to tune carefully. Set it too tight and you'll get false positives on legitimate complex queries; set it too loose and it won't catch real regressions. Start with 2–3× your observed baseline cost on a representative query set, then tighten over time as you build confidence in your agent's behavior.

---

## Putting It All Together

Cost runaway in tool-using agents is a silent killer — the agent looks healthy in your evals, users get correct answers, and the only signal is a billing alert you might not have set up yet. The pattern described here gives you three layers of defense: a caching layer that prevents redundant calls from reaching the API at all, hard executor limits that stop runaway loops before they exhaust your budget, and a CI test that makes cost efficiency a first-class regression signal alongside correctness.

---

Get 5 ready-to-run evaluation cases free at [github.com/weiseer/ai-agent-qa-eval-pack-starter](https://github.com/weiseer/ai-agent-qa-eval-pack-starter) · full 23-case pack at [gumroad.com/l/dcipxt](https://gumroad.com/l/dcipxt) · new cases by email at [dl.weiseer.com/cases](https://dl.weiseer.com/cases)

---

The test suite is the most durable part of this approach. Prompt changes, model upgrades, and new tool additions all have the potential to reintroduce inefficiency — and running `test_tool_call_efficiency` on every merge means you find out about cost regressions in a pull request, not on a Monday morning invoice. Treating tool-call efficiency as a first-class regression signal, on equal footing with correctness, is the engineering habit that keeps agentic systems economically viable as they scale.