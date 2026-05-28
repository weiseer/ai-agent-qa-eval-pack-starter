"""Example adapter: a LangChain/LangGraph agent -> agent-eval.

  agent-eval run --cases ./cases --adapter examples.langchain_adapter:agent

LangChain AgentExecutor exposes intermediate_steps = [(AgentAction, observation)].
Map each AgentAction.tool / .tool_input to a ToolCall so trace cases work.
"""
from __future__ import annotations

from agent_eval_runner import AgentResult, ToolCall

# from langchain.agents import AgentExecutor   # your real executor
# executor: AgentExecutor = build_my_agent()


def agent(case: dict) -> AgentResult:
    inp = case["input"]
    prompt = inp["user_message"]
    if inp.get("context"):
        prompt += f"\n\n[context]\n{inp['context']}"

    # Run YOUR executor with intermediate steps returned:
    #   result = executor.invoke({"input": prompt},
    #                            config={"return_intermediate_steps": True})
    # Replace the next two lines with the real call:
    result = {"output": "REPLACE_WITH_executor.invoke(...)", "intermediate_steps": []}

    trace = [
        ToolCall(name=action.tool, args=(action.tool_input if isinstance(action.tool_input, dict)
                                         else {"input": action.tool_input}))
        for action, _obs in result.get("intermediate_steps", [])
    ]
    return AgentResult(output_text=result.get("output", ""), trace=trace)
