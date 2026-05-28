# How to Test Whether Your AI Agent Calls the Right Tool (Instead of Hallucinating)

Your agent has 12 tools registered. You ask it to look up a customer's order status. It calls `search_knowledge_base` instead of `get_order_status`. No error is thrown — the agent returns a plausible-sounding text response. You might ship it without realizing the mistake.

This is the most common silent failure mode in tool-using agents, and many teams lack a systematic way to catch it.

---

## Why Tool Selection Fails

LLMs don't "know" which tool to call — they predict the most likely next token given the prompt. That means:

- **Ambiguous tool descriptions** → wrong tool selected
- **Too many tools** → model picks the nearest semantic match
- **Prompt drift** (system prompt changes) → previously correct selections break
- **Model version updates** → behavior shifts silently

You can't catch this with unit tests on your tool implementations. You need eval cases that assert *which tool was invoked*, not just whether the final answer looks okay.

---

## The Test Structure You Need

Each test case needs three things:

1. **Input** — the user message (and optionally conversation history)
2. **Expected tool call** — name + key arguments
3. **Pass condition** — exact match, partial match, or "must not call X"

Here's a concrete YAML format that works well for this:

```yaml
# tool_selection_tests.yaml

- id: order_status_lookup
  description: "Agent should call get_order_status, not search_knowledge_base"
  input:
    user_message: "Where is my order #ORD-9921?"
  expected_tool_call:
    name: get_order_status
    arguments:
      order_id: "ORD-9921"
  match_mode: exact_name_partial_args
  must_not_call:
    - search_knowledge_base
    - get_product_info

- id: refund_eligibility_check
  description: "Refund question should route to check_refund_policy, not create_ticket"
  input:
    user_message: "Can I get a refund for an order I placed 40 days ago?"
  expected_tool_call:
    name: check_refund_policy
  match_mode: exact_name_only

- id: ambiguous_product_question
  description: "Generic product question — acceptable to call either search tool"
  input:
    user_message: "Tell me about your return policy"
  expected_tool_call:
    name: search_knowledge_base
  match_mode: exact_name_only
```

> **Note on `match_mode`:** The harness below supports two modes — `exact_name_only` and `exact_name_partial_args`. Unrecognized values default to `exact_name_only` and log a warning rather than silently passing.

---

## Running This Against a Real Agent

Here's a minimal Python harness using OpenAI function calling. Two important notes before you use this:

1. **Include your real system prompt.** The `run_agent_get_tool_call` function uses a placeholder — your evals must use the same system prompt your production agent uses, otherwise you're not testing real behavior.
2. **Add retries and error handling** before running this in CI.

```python
import yaml
import json
from openai import OpenAI

client = OpenAI()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Look up order status by order ID",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search support articles and FAQs",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_refund_policy",
            "description": "Check refund eligibility",
            "parameters": {
                "type": "object",
                "properties": {"days_since_purchase": {"type": "integer"}},
                "required": ["days_since_purchase"],
            },
        },
    },
]

SYSTEM_PROMPT = "You are a customer support agent. Use the available tools to answer questions."

KNOWN_MATCH_MODES = {"exact_name_only", "exact_name_partial_args"}


def run_agent_get_tool_call(user_message: str) -> dict | None:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        tools=TOOLS,
        tool_choice="auto",
    )
    msg = response.choices[0].message
    if msg.tool_calls:
        tc = msg.tool_calls[0]
        return {"name": tc.function.name, "arguments": json.loads(tc.function.arguments)}
    return None


def evaluate(test_cases: list) -> int:
    passed, failed = 0, 0

    for case in test_cases:
        actual = run_agent_get_tool_call(case["input"]["user_message"])
        expected = case["expected_tool_call"]
        must_not = case.get("must_not_call", [])
        match_mode = case.get("match_mode", "exact_name_only")

        if match_mode not in KNOWN_MATCH_MODES:
            print(f"WARN [{case['id']}]: unrecognized match_mode '{match_mode}', defaulting to exact_name_only")

        # Check forbidden tools
        if actual and actual["name"] in must_not:
            print(f"FAIL [{case['id']}]: called forbidden tool '{actual['name']}'")
            failed += 1
            continue

        # Check expected tool name
        if not actual or actual["name"] != expected["name"]:
            actual_name = actual["name"] if actual else "None"
            print(f"FAIL [{case['id']}]: expected '{expected['name']}', got '{actual_name}'")
            failed += 1
            continue

        # Partial argument check
        if match_mode == "exact_name_partial_args":
            for k, v in expected.get("arguments", {}).items():
                if str(actual["arguments"].get(k)) != str(v):
                    print(f"FAIL [{case['id']}]: arg '{k}' expected '{v}', got '{actual['arguments'].get(k)}'")
                    failed += 1
                    break
            else:
                print(f"PASS [{case['id']}]")
                passed += 1
        else:
            print(f"PASS [{case['id']}]")
            passed += 1

    print(f"\n{passed} passed, {failed} failed out of {passed + failed} cases")
    return failed


if __name__ == "__main__":
    with open("tool_selection_tests.yaml") as f:
        cases = yaml.safe_load(f)
    exit_code = evaluate(cases)
    raise SystemExit(exit_code)
```

Running this against the three YAML cases above produces output like:

```
PASS [order_status_lookup]
PASS [refund_eligibility_check]
PASS [ambiguous_product_question]

3 passed, 0 failed out of 3 cases
```

Any failure prints the exact mismatch — wrong tool name, forbidden tool called, or argument value off — so you know immediately what to fix.

---

## What to Do When a Case Fails

A failing case tells you one of three things:

- **Tool description is ambiguous** — the model couldn't distinguish it from a semantically similar tool. Rewrite the description to be more specific about when *not* to use it.
- **System prompt is overriding tool selection** — instructions like "always search before responding" can override correct routing. Audit your prompt for implicit biases.
- **The model genuinely can't extract the argument** — for cases like `days_since_purchase` from natural language, consider whether your tool signature is realistic, or whether a pre-processing step should handle extraction before the tool call.

The test output gives you a precise failure signal. The fix almost always lives in your tool descriptions or system prompt — not in your tool implementations.

---

## Scaling This Up

Three cases won't cover a real agent. A production-grade eval suite for a customer support agent typically needs:

- **Happy path cases** for every tool (correct routing with clean input)
- **Adversarial cases** — inputs designed to trigger the wrong tool
- **Boundary cases** — ambiguous phrasing where the correct tool is non-obvious
- **Must-not-call cases** — sensitive tools (e.g., `cancel_order`) that should never fire on ambiguous input

That's usually 20–30 cases minimum before you have meaningful coverage. The structure stays identical — more YAML entries, same harness.

---

## Summary

Silent tool misrouting is one of the hardest agent bugs to catch because it produces no exceptions and often generates plausible-looking output. The fix is straightforward: define expected tool calls as structured test cases, run them against your real agent on every prompt or model change, and treat failures as regressions. The harness above is the minimum viable version — extend it with your actual tools, your real system prompt, and enough cases to cover the failure modes that matter for your use case.

---

Free 5-case starter pack: [github.com/weiseer/ai-agent-qa-eval-pack-starter](https://github.com/weiseer/ai-agent-qa-eval-pack-starter) · Full 23-case pack: [gumroad.com/l/dcipxt](https://gumroad.com/l/dcipxt) · New cases by email: [dl.weiseer.com/cases](https://dl.weiseer.com/cases)

---

Tool selection failures are fundamentally a specification problem: the model can only route correctly if your tool descriptions unambiguously encode when each tool should and shouldn't be used. Building a structured eval suite forces you to make those boundaries explicit — and running it on every model or prompt change turns what was an invisible regression risk into a measurable, fixable signal.