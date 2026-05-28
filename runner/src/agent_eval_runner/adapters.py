"""Adapters connect the runner to YOUR agent.

Two ways to use the runner:

1. CUSTOM ADAPTER (recommended, works for all 5 methods incl. trace_*):
   Write a function that takes a case dict and returns an AgentResult.
   Point the CLI at it:  --adapter my_module:my_agent

   def my_agent(case: dict) -> AgentResult:
       inp = case["input"]
       resp, tool_calls = run_my_real_agent(
           system=inp.get("system_message"),
           user=inp["user_message"],
           context=inp.get("context"),
       )
       return AgentResult(
           output_text=resp,
           trace=[ToolCall(name=tc.name, args=tc.args) for tc in tool_calls],
       )

2. BUILT-IN DIRECT ADAPTER (zero-code demo, text methods only):
   --adapter openai:gpt-4o   or   --adapter anthropic:claude-sonnet-4-6
   Runs the case prompt straight against the model. Good for keyword_match /
   regex_match / refusal_detection. trace_* cases need your real agent (option 1).
"""
from __future__ import annotations

import importlib
import os
from typing import Any, Callable

from .models import AgentResult, ToolCall

Adapter = Callable[[dict[str, Any]], AgentResult]


def _messages(case: dict) -> list[dict[str, str]]:
    inp = case.get("input", {})
    msgs: list[dict[str, str]] = []
    if inp.get("system_message"):
        msgs.append({"role": "system", "content": inp["system_message"]})
    for h in inp.get("conversation_history", []) or []:
        msgs.append({"role": h["role"], "content": h["content"]})
    user = inp["user_message"]
    ctx = inp.get("context")
    if ctx:
        user = f"{user}\n\n[context]\n{ctx}"
    msgs.append({"role": "user", "content": user})
    return msgs


def _openai_adapter(model: str) -> Adapter:
    from openai import OpenAI  # lazy import
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def run(case: dict) -> AgentResult:
        msgs = _messages(case)
        resp = client.chat.completions.create(model=model, messages=msgs, temperature=0)
        return AgentResult(output_text=resp.choices[0].message.content or "")
    return run


def _anthropic_adapter(model: str) -> Adapter:
    from anthropic import Anthropic  # lazy import
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def run(case: dict) -> AgentResult:
        msgs = _messages(case)
        system = ""
        chat = []
        for m in msgs:
            if m["role"] == "system":
                system += m["content"] + "\n"
            else:
                chat.append({"role": "user" if m["role"] in ("user", "tool") else "assistant",
                             "content": m["content"]})
        resp = client.messages.create(model=model, max_tokens=1024, system=system or None, messages=chat)
        text = "".join(b.text for b in resp.content if hasattr(b, "text"))
        return AgentResult(output_text=text)
    return run


def resolve_adapter(spec: str) -> Adapter:
    """Resolve an --adapter spec to a callable.

    Forms:
      'openai:MODEL'      -> built-in direct OpenAI adapter (text methods)
      'anthropic:MODEL'   -> built-in direct Anthropic adapter (text methods)
      'my.module:func'    -> your custom adapter function (all methods)
    """
    if spec.startswith("openai:"):
        return _openai_adapter(spec.split(":", 1)[1])
    if spec.startswith("anthropic:"):
        return _anthropic_adapter(spec.split(":", 1)[1])
    if ":" not in spec:
        raise ValueError(f"adapter spec must be 'module:func' or 'openai:MODEL' / 'anthropic:MODEL', got {spec!r}")
    mod_name, func_name = spec.rsplit(":", 1)
    mod = importlib.import_module(mod_name)
    fn = getattr(mod, func_name)
    if not callable(fn):
        raise TypeError(f"{spec} is not callable")
    return fn
