"""agent-eval-runner — run the AI Agent QA Eval Pack against your agent.

Public API for writing custom adapters:
    from agent_eval_runner import AgentResult, ToolCall
"""
from .models import AgentResult, ToolCall, EvalResult
from .evaluators import evaluate
from .loader import load_cases

__version__ = "0.3.1"
__all__ = ["AgentResult", "ToolCall", "EvalResult", "evaluate", "load_cases"]
