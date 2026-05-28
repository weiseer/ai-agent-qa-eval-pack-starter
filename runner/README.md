# agent-eval-runner

Run the **AI Agent QA Eval Pack** (vendor-agnostic YAML eval cases) against your
tool-using LLM agent. **Deterministic** checks — no LLM-as-judge — so the report
is defensible for production sign-off. Cross-platform (pure Python: Win / macOS / Linux).

## Install

```bash
pip install agent-eval-runner            # core
pip install "agent-eval-runner[openai]"  # + built-in OpenAI demo adapter
pip install "agent-eval-runner[anthropic]"
```

## 30-second demo (no code)

Run text-based cases straight against a model:

```bash
export OPENAI_API_KEY=sk-...
agent-eval run --cases ./cases --adapter openai:gpt-4o --dimension safety
```

## Real usage (all 5 case types, incl. tool-trace assertions)

Write a 10-line adapter wrapping *your* agent:

```python
# my_adapter.py
from agent_eval_runner import AgentResult, ToolCall

def agent(case: dict) -> AgentResult:
    inp = case["input"]
    final_text, tool_calls = run_my_agent(           # <- your agent
        system=inp.get("system_message"),
        user=inp["user_message"],
        context=inp.get("context"),
    )
    return AgentResult(
        output_text=final_text,
        trace=[ToolCall(name=c.name, args=c.args) for c in tool_calls],
    )
```

```bash
agent-eval run --cases ./cases --adapter my_adapter:agent --report signoff.md
```

Exit code is **non-zero if any high-severity case fails** — drop it straight into CI.

## What it checks

| method | what it asserts |
|---|---|
| `keyword_match` | required / forbidden substrings in the answer |
| `regex_match` | answer matches a regex |
| `refusal_detection` | agent refused (or complied) as expected |
| `trace_count` | tool-call counts, required/forbidden tools, args seen |
| `trace_invariant` | structural: no error-loops, parallel-when-possible, step caps |

## Output

- Terminal pass/fail summary grouped by dimension, with production-blockers flagged
- `--report out.md` → a Markdown sign-off report (share with your team / customer)

---
Full 23-case pack: **https://weiseer.gumroad.com/l/dcipxt** ·
Free 5-case starter: **https://github.com/weiseer/ai-agent-qa-eval-pack-starter**
