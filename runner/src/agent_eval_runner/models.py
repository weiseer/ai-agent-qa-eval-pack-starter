"""Core data types for the eval runner."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """One tool/function invocation in the agent's trace.

    Provide `error=True` if the tool returned/raised an error, and
    `parallel_group` (same int for calls issued in parallel) to enable the
    richer trace_invariant checks. Both optional — text/count methods don't need them.
    """
    name: str
    args: dict[str, Any] = field(default_factory=dict)
    error: bool = False
    parallel_group: int | None = None


@dataclass
class AgentResult:
    """What your agent returned for one case.

    output_text: the agent's final text answer (used by keyword/regex/refusal).
    trace: ordered tool calls the agent made (used by trace_count/trace_invariant).
    """
    output_text: str = ""
    trace: list[ToolCall] = field(default_factory=list)


@dataclass
class EvalResult:
    case_id: str
    dimension: str
    severity: str
    title: str
    method: str
    passed: bool
    score: float
    detail: str
