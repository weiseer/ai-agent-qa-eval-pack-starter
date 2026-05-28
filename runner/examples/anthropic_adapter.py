"""Example adapter: an Anthropic tool-use agent -> agent-eval.

  agent-eval run --cases ./cases --adapter examples.anthropic_adapter:agent

Return final text + ordered tool calls so trace_count / trace_invariant work.
"""
from __future__ import annotations

from anthropic import Anthropic

from agent_eval_runner import AgentResult, ToolCall

client = Anthropic()  # reads ANTHROPIC_API_KEY

# --- wire your real tools here (Anthropic tool schema) ---
TOOLS: list[dict] = [
    # {"name": "get_order_status", "description": "...",
    #  "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}}}},
]


def run_tool(name: str, args: dict) -> str:
    return "TOOL_RESULT_PLACEHOLDER"


def agent(case: dict) -> AgentResult:
    inp = case["input"]
    system = inp.get("system_message") or ""
    messages: list[dict] = []
    for h in inp.get("conversation_history", []) or []:
        role = "user" if h["role"] in ("user", "tool") else "assistant"
        messages.append({"role": role, "content": h["content"]})
    user = inp["user_message"]
    if inp.get("context"):
        user += f"\n\n[context]\n{inp['context']}"
    messages.append({"role": "user", "content": user})

    trace: list[ToolCall] = []
    for _ in range(8):
        resp = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=1024,
            system=system or None, messages=messages, tools=TOOLS or [])
        tool_uses = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
        text = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", None) == "text")
        if tool_uses:
            messages.append({"role": "assistant", "content": resp.content})
            results = []
            for tu in tool_uses:
                trace.append(ToolCall(name=tu.name, args=dict(tu.input or {})))
                results.append({"type": "tool_result", "tool_use_id": tu.id,
                                "content": run_tool(tu.name, dict(tu.input or {}))})
            messages.append({"role": "user", "content": results})
            continue
        return AgentResult(output_text=text, trace=trace)
    return AgentResult(output_text="(tool loop exhausted)", trace=trace)
