"""Example adapter: an OpenAI tool-calling agent -> agent-eval.

Copy this, wire in YOUR tools (TOOLS + run_tool), then:
  agent-eval run --cases ./cases --adapter examples.openai_adapter:agent --report signoff.md

The runner calls `agent(case)` once per case. You return what your agent did:
final text + the ordered tool calls (so trace_count / trace_invariant cases work).
"""
from __future__ import annotations

import json

from openai import OpenAI

from agent_eval_runner import AgentResult, ToolCall

client = OpenAI()  # reads OPENAI_API_KEY

# --- wire your real tools here ---
TOOLS: list[dict] = [
    # {"type": "function", "function": {"name": "get_order_status",
    #   "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}}}}},
]


def run_tool(name: str, args: dict) -> str:
    """Execute your tool. For eval, you may honor case context.mock_tool_behavior."""
    return "TOOL_RESULT_PLACEHOLDER"


def agent(case: dict) -> AgentResult:
    inp = case["input"]
    messages: list[dict] = []
    if inp.get("system_message"):
        messages.append({"role": "system", "content": inp["system_message"]})
    for h in inp.get("conversation_history", []) or []:
        messages.append({"role": h["role"], "content": h["content"]})
    user = inp["user_message"]
    if inp.get("context"):
        user += f"\n\n[context]\n{inp['context']}"
    messages.append({"role": "user", "content": user})

    trace: list[ToolCall] = []
    for _ in range(8):  # bounded tool loop
        resp = client.chat.completions.create(
            model="gpt-4o", messages=messages, tools=TOOLS or None, temperature=0)
        msg = resp.choices[0].message
        if msg.tool_calls:
            messages.append(msg.model_dump())
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments or "{}")
                trace.append(ToolCall(name=tc.function.name, args=args))
                result = run_tool(tc.function.name, args)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            continue
        return AgentResult(output_text=msg.content or "", trace=trace)
    return AgentResult(output_text="(tool loop exhausted)", trace=trace)
