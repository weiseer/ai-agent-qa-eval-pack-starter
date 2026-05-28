# AI Agent QA Eval Pack — Free Starter (5 cases)

> Vendor-agnostic eval cases for tool-using LLM agents (LangChain / OpenAI
> function calling / Anthropic tool use / custom loops). Read them like
> documentation, run them against your agent, record pass/fail.

**⭐ If this is useful, star the repo** — it's the only signal that tells me
which dimensions to expand next, and it helps other agent builders find it.

**📬 Want new cases + the 6-dimension cheatsheet as they ship?**
Drop your email (no spam, just new eval cases): **https://dl.weiseer.com/cases**

---

## Run your first eval in 5 minutes

Don't read all five files first. Do one:

1. Open `cases/dim_4_prompt_injection/case_01_tool_response_injection.yaml`
   (the OWASP LLM01 one — the case most agents quietly fail).
2. Copy `input.system_message` + `input.user_message` +
   `input.context.mock_tool_behavior` into your agent.
3. Watch the tool-call trace. Compare against the `expected` block.
4. Did your agent treat adversarial text *inside the tool response* as
   instructions? If yes — that's a real prod vulnerability you just found
   for free.

If that one case surfaced something, the other four will too.

---

## What's inside (5 cases, 5 of 6 dimensions)

| Case | Dimension | Failure mode probed |
|---|---|---|
| `dim_1_accuracy/case_01_tool_selection.yaml` | accuracy | Agent skips the tool, hallucinates from training |
| `dim_2_safety/case_01_refuse_harmful_tool_use.yaml` | safety | Refuses harmful tool use even under "justification" framing |
| `dim_3_edge_cases/case_01_tool_timeout.yaml` | edge_cases | Graceful recovery from persistent tool failure |
| `dim_4_prompt_injection/case_01_tool_response_injection.yaml` | prompt_injection | **OWASP LLM01** — adversarial content inside tool responses |
| `dim_6_cost_efficiency/case_01_redundant_tool_calls.yaml` | cost_efficiency | Avoids redundant tool calls, supports parallel |

Schema: `schema/eval_case.schema.yaml`.

---

## Free starter vs full pack — what you're actually buying

The free 5 cases tell you **whether** your agent has gaps. The paid pack is
what you use to **sign off an agent for production**:

| | Free starter | Full pack v1.1 |
|---|---|---|
| Cases | 5 (1 per dim, 5 dims) | **23** across all 6 dims |
| Prompt-injection coverage | 1 case | 4 cases (OWASP LLM01 weighted) |
| Hallucination dimension | — | 4 cases incl. predicted-vs-actual drift |
| Cost dimension | 1 case | 5 cases incl. cost-cap enforcement + parallel-worker diversity |
| **Customer-deliverable report template** | — | ✅ Markdown sign-off report |
| Real provenance | — | Cases derived from dogfooding a live production agent |

**Why the paid coverage matters:** the gaps that get agents pulled from prod
aren't in the obvious dimensions — they're in hallucination drift and cost
runaway under load. Those are the cases the free starter doesn't include.

🎉 **Launch promo through 2026-06-03 22:00 BJT** — `LAUNCH7` = $20 off (effective **$29**).

**→ Get the full pack: https://weiseer.gumroad.com/l/dcipxt** (code `LAUNCH7`)

🇨🇳 **中国大陆**：Gumroad 国内卡/VPN 常被 Stripe 风控拦。微信/支付宝走
**https://dl.weiseer.com/pay**（同内容，24h 内人工交付，同 7 天退款；促销 ¥199 vs ¥350）。

---

## How to use (any case)

1. Open any `cases/.../case_*.yaml`
2. Read `input.user_message` + `input.system_message` + `input.context.mock_tool_behavior`
3. Send equivalent input to your agent
4. Compare your agent's tool-call trace + final output against `expected`
5. Mark pass/fail (report template in the full pack)

Trace-based cases need your agent to expose its tool-call sequence — native
in Anthropic `tool_use` blocks and OpenAI `tool_calls` arrays.

---

## License

Free starter cases + schema: **CC BY 4.0** — copy, modify, integrate.
Attribution requested, not required. Full paid pack: per-purchase single-team license.

## References

- [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/)
- [Anthropic: Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [OpenAI function calling docs](https://platform.openai.com/docs/guides/function-calling)

---

Built by Weiseer — a solo founder dogfooding this on a real production agent.
Found a bug, want a dimension expanded, or have feedback? Open an issue, or
reply to the free email drop above. I read everything.
