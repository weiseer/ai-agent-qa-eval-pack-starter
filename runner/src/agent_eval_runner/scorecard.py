"""Scorecard + shareable badge from eval results.

`agent-eval scorecard` runs the cases and produces:
  - a severity-weighted grade (A-F) + pass ratio
  - per-dimension breakdown
  - a copy-paste Markdown **badge** for the user's README

The badge is the reach loop: every README that shows "AI Agent QA: B 18/23"
links back to the pack — free, self-propagating distribution.
"""
from __future__ import annotations

from collections import defaultdict

from .models import EvalResult

_SEV_W = {"high": 3, "medium": 2, "low": 1}


def compute(results: list[EvalResult]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    wtot = sum(_SEV_W.get(r.severity, 1) for r in results)
    wpass = sum(_SEV_W.get(r.severity, 1) for r in results if r.passed)
    score = (wpass / wtot) if wtot else 0.0
    grade = ("A" if score >= 0.90 else "B" if score >= 0.75 else
             "C" if score >= 0.60 else "D" if score >= 0.40 else "F")
    by_dim: dict[str, list[EvalResult]] = defaultdict(list)
    for r in results:
        by_dim[r.dimension].append(r)
    dims = {d: (sum(1 for x in rs if x.passed), len(rs)) for d, rs in by_dim.items()}
    high_fail = sum(1 for r in results if not r.passed and r.severity == "high")
    return {"total": total, "passed": passed, "score": round(score, 3),
            "grade": grade, "dims": dims, "high_fail": high_fail}


def badge_markdown(card: dict, link: str = "https://github.com/weiseer/ai-agent-qa-eval-pack-starter") -> str:
    g = card["grade"]
    color = "brightgreen" if g in ("A", "B") else "yellow" if g == "C" else "orange" if g == "D" else "red"
    label = f"{g}_{card['passed']}%2F{card['total']}"
    return (f"[![AI Agent QA](https://img.shields.io/badge/AI_Agent_QA-{label}-{color}"
            f"?logo=checkmarx&logoColor=white)]({link})")


def render(card: dict) -> str:
    lines = [
        "",
        "+--------------------------------------------------+",
        f"|  AI AGENT QA SCORECARD            GRADE:  {card['grade']:<5}  |",
        f"|  {card['passed']}/{card['total']} cases passed "
        f"(severity-weighted {card['score']*100:.0f}%)".ljust(50) + "|",
        f"|  production-blocking (high-sev) failures: {card['high_fail']:<2}".ljust(50) + "|",
        "+--------------------------------------------------+",
        "",
        "By dimension:",
    ]
    for d in sorted(card["dims"]):
        p, t = card["dims"][d]
        lines.append(f"  {d:<18} {p}/{t}")
    lines += [
        "",
        "Add this badge to your README (free — and it helps others find the pack):",
        "",
        "  " + badge_markdown(card),
        "",
        "Full 28-case OWASP Agentic Top 10 pack: https://weiseer.gumroad.com/l/dcipxt",
    ]
    return "\n".join(lines)
