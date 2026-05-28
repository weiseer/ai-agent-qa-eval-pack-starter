"""Render eval results to terminal + a Markdown sign-off report."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from .models import EvalResult


def terminal_summary(results: list[EvalResult]) -> str:
    lines = []
    by_dim: dict[str, list[EvalResult]] = defaultdict(list)
    for r in results:
        by_dim[r.dimension].append(r)
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    for dim in sorted(by_dim):
        rs = by_dim[dim]
        p = sum(1 for r in rs if r.passed)
        lines.append(f"\n  {dim}: {p}/{len(rs)} passed")
        for r in rs:
            mark = "PASS" if r.passed else "FAIL"
            sev = f"[{r.severity}]"
            lines.append(f"    {mark} {sev:8} {r.case_id}  {r.title[:48]}")
            if not r.passed:
                lines.append(f"         -> {r.detail}")
    pct = (passed / total * 100) if total else 0
    head = f"\n{'='*60}\nAI Agent Eval — {passed}/{total} passed ({pct:.0f}%)\n{'='*60}"
    # high-severity failures are the production-blockers
    high_fail = [r for r in results if not r.passed and r.severity == "high"]
    tail = f"\n\n{'!'*60}\nPRODUCTION-BLOCKING (high-severity failures): {len(high_fail)}\n"
    for r in high_fail:
        tail += f"  - {r.case_id} {r.title[:50]}\n"
    tail += "!"*60 if high_fail else "No high-severity failures."
    return head + "".join(lines) + tail


def markdown_report(results: list[EvalResult], agent_label: str = "agent") -> str:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    pct = (passed / total * 100) if total else 0
    high_fail = [r for r in results if not r.passed and r.severity == "high"]
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    md = [f"# AI Agent QA Eval Report — {agent_label}",
          f"\n_Generated {ts} · {passed}/{total} passed ({pct:.0f}%) · "
          f"{len(high_fail)} production-blocking failure(s)_\n",
          "## Sign-off summary\n",
          "| Dimension | Passed | Total |", "|---|---|---|"]
    by_dim: dict[str, list[EvalResult]] = defaultdict(list)
    for r in results:
        by_dim[r.dimension].append(r)
    for dim in sorted(by_dim):
        rs = by_dim[dim]
        md.append(f"| {dim} | {sum(1 for r in rs if r.passed)} | {len(rs)} |")
    if high_fail:
        md.append("\n## ⛔ Production-blocking failures (high severity)\n")
        for r in high_fail:
            md.append(f"- **{r.case_id}** — {r.title}\n  - {r.detail}")
    md.append("\n## Full results\n")
    md.append("| Result | Severity | Case | Method | Detail |")
    md.append("|---|---|---|---|---|")
    for r in sorted(results, key=lambda x: (x.passed, x.dimension)):
        mark = "✅ PASS" if r.passed else "❌ FAIL"
        det = r.detail.replace("|", "\\|")[:120]
        md.append(f"| {mark} | {r.severity} | {r.case_id} | {r.method} | {det} |")
    md.append("\n---\n_AI Agent QA Eval Pack · deterministic eval, no LLM-judge · "
              "weiseer.gumroad.com/l/dcipxt_")
    return "\n".join(md)
