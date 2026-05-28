"""Mock adapter for smoke-testing the runner without API calls.

Returns canned responses keyed off the case dimension so you can see PASS/FAIL
mechanics end-to-end. NOT for real evaluation — replace with an adapter that
calls your actual agent.

  agent-eval run --cases ./cases --adapter examples.mock_adapter:agent
"""
from __future__ import annotations

from agent_eval_runner import AgentResult, ToolCall


def agent(case: dict) -> AgentResult:
    dim = case.get("dimension")
    exp = case.get("expected", {})

    if dim == "safety":
        # pretend the agent correctly refuses
        return AgentResult(output_text="I'm sorry, but I can't help with that request.")

    if dim in ("accuracy", "cost_efficiency", "edge_cases"):
        # pretend a single clean tool call
        return AgentResult(
            output_text="Done. " + " ".join(exp.get("must_contain", [])[:1]),
            trace=[ToolCall(name="get_order_status", args={"order_id": "123"})],
        )

    # default: echo any required substrings so keyword cases pass
    return AgentResult(output_text="Here is the answer. " + " ".join(exp.get("must_contain", [])))
