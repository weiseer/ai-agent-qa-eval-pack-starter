"""agent-eval CLI — run the AI Agent QA Eval Pack against your agent.

  agent-eval run --cases ./cases --adapter my_module:my_agent
  agent-eval run --cases ./cases --adapter openai:gpt-4o --report out.md
  agent-eval list --cases ./cases

Cross-platform: pure Python (argparse + pyyaml). No OS-specific code.
"""
from __future__ import annotations

import argparse
import sys

from .adapters import resolve_adapter
from .evaluators import evaluate
from .loader import load_cases
from .models import AgentResult
from .report import markdown_report, terminal_summary
from . import scorecard as _scorecard_mod


def _run(args: argparse.Namespace) -> int:
    cases = load_cases(args.cases)
    if args.dimension:
        cases = [c for c in cases if c.get("dimension") == args.dimension]
    if not cases:
        print("no cases found", file=sys.stderr)
        return 2
    try:
        adapter = resolve_adapter(args.adapter)
    except Exception as e:
        print(f"adapter error: {e}", file=sys.stderr)
        return 2

    results = []
    for c in cases:
        try:
            out = adapter(c)
            if not isinstance(out, AgentResult):
                raise TypeError("adapter must return AgentResult")
        except Exception as e:
            print(f"  [{c.get('id')}] adapter raised: {e}", file=sys.stderr)
            out = AgentResult(output_text=f"<adapter error: {e}>")
        results.append(evaluate(c, out))

    print(terminal_summary(results))
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(markdown_report(results, agent_label=args.label or args.adapter))
        print(f"\nMarkdown report written: {args.report}")

    failed = sum(1 for r in results if not r.passed)
    high_fail = sum(1 for r in results if not r.passed and r.severity == "high")
    # exit non-zero if any high-severity failure (CI-friendly gate)
    return 1 if high_fail else 0


def _list(args: argparse.Namespace) -> int:
    for c in load_cases(args.cases):
        print(f"{c.get('id'):16} [{c.get('severity'):6}] {c.get('dimension'):16} {c.get('title','')[:50]}")
    return 0


def _scorecard(args: argparse.Namespace) -> int:
    cases = load_cases(args.cases)
    if not cases:
        print("no cases found", file=sys.stderr)
        return 2
    try:
        adapter = resolve_adapter(args.adapter)
    except Exception as e:
        print(f"adapter error: {e}", file=sys.stderr)
        return 2
    results = []
    for c in cases:
        try:
            out = adapter(c)
            if not isinstance(out, AgentResult):
                raise TypeError("adapter must return AgentResult")
        except Exception as e:
            out = AgentResult(output_text=f"<adapter error: {e}>")
        results.append(evaluate(c, out))
    card = _scorecard_mod.compute(results)
    print(_scorecard_mod.render(card))
    if args.badge:
        with open(args.badge, "w", encoding="utf-8") as f:
            f.write(_scorecard_mod.badge_markdown(card) + "\n")
        print(f"\nbadge markdown written: {args.badge}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="agent-eval", description="Run AI Agent QA Eval Pack against your agent.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("run", help="run cases against your agent")
    pr.add_argument("--cases", required=True, help="path to the cases/ directory")
    pr.add_argument("--adapter", required=True, help="module:func | openai:MODEL | anthropic:MODEL")
    pr.add_argument("--dimension", help="only run one dimension (e.g. prompt_injection)")
    pr.add_argument("--report", help="write a Markdown sign-off report to this path")
    pr.add_argument("--label", help="agent label for the report")
    pr.set_defaults(func=_run)

    pl = sub.add_parser("list", help="list available cases")
    pl.add_argument("--cases", required=True)
    pl.set_defaults(func=_list)

    psc = sub.add_parser("scorecard", help="grade your agent + emit a shareable README badge")
    psc.add_argument("--cases", required=True)
    psc.add_argument("--adapter", required=True, help="module:func | openai:MODEL | anthropic:MODEL")
    psc.add_argument("--badge", help="write the Markdown badge snippet to this file")
    psc.set_defaults(func=_scorecard)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
