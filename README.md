# AI Agent QA Eval Pack — Free Starter (5 cases)

A free 5-case sampler of the **AI Agent QA Eval Pack** — production-ready
test cases for tool-using AI agents (LangChain agents, OpenAI function
calling, Anthropic tool use, custom agent loops).

If your agent calls tools and you don't have a systematic eval workflow,
this is a vendor-agnostic, framework-agnostic starting point. Read the
YAML cases like documentation, run them against your agent, record
pass / fail.

## What's inside

5 hand-crafted test cases across 5 of the 6 dimensions covered by the
full pack:

| Case | Dimension | Failure mode probed |
|---|---|---|
| `cases/dim_1_accuracy/case_01_tool_selection.yaml` | accuracy | Agent skips the tool and hallucinates from training instead of calling the available tool |
| `cases/dim_2_safety/case_01_refuse_harmful_tool_use.yaml` | safety | Refuses harmful tool use even when user wraps it in a "justification" frame |
| `cases/dim_3_edge_cases/case_01_tool_timeout.yaml` | edge_cases | Graceful recovery from persistent tool failure — no infinite retry, no fabricated fallback |
| `cases/dim_4_prompt_injection/case_01_tool_response_injection.yaml` | prompt_injection | **OWASP LLM01** — adversarial content **inside tool responses** (web search snippets, RAG context) trying to hijack the agent |
| `cases/dim_6_cost_efficiency/case_01_redundant_tool_calls.yaml` | cost_efficiency | Avoids redundant tool calls; supports parallel where the API supports it |

Schema for the case format: `schema/eval_case.schema.yaml`.

## How to use

1. Open any `cases/.../case_*.yaml`
2. Read `input.user_message` + `input.system_message` + (if present) `input.context.mock_tool_behavior`
3. Send equivalent input to your agent
4. Compare your agent's tool-call trace + final output against the `expected` block
5. Mark pass/fail in your own ledger (or use the report template in the
   full pack)

For trace-based cases (most of these), your agent must expose its
tool-call sequence (tool name + args). Native in Anthropic `tool_use`
blocks and OpenAI `tool_calls` arrays.

## What's in the full pack ($49)

The **AI Agent QA Eval Pack v1.0** ships **20 cases** across 6 dimensions:

- 3 cases per dimension (accuracy / safety / hallucination / cost_efficiency)
- 4 cases per dimension (edge_cases / prompt_injection — weighted for
  OWASP LLM01 coverage)
- Hallucination dimension (3 cases — workflow checks: did the agent
  actually call the tool, or fake a recall?) — NOT in this starter
- Customer-delivered Markdown report template
- Pro tier preview (Standard / Pro waitlist v1.1+)

Get the full pack: **`https://weiseer.gumroad.com/l/dcipxt`**

## License

Cases + schema in this free starter: **CC BY 4.0** — you may copy,
modify, and integrate into your own eval workflow. Attribution requested
but not required.

The full paid pack uses a different license (per-purchase, single-team
use).

## References

Each case file's `references` block links to the source material:

- [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/)
- [Anthropic: Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [OpenAI function calling docs](https://platform.openai.com/docs/guides/function-calling)

---

Maintained by Weiseer. Found a bug, want a dimension expanded, or have
feedback? Reply to the email you received with your purchase, or open
an issue in this repo.
