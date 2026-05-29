---
layout: default
title: "How to test when OpenAI function calling passes malformed or wrong arguments to a function"
description: "Catch and test the failure mode where OpenAI function calling passes malformed or wrong arguments to a function — a deterministic eval + one-command runner"
---

# How to test when OpenAI function calling passes malformed or wrong arguments to a function

When OpenAI function calling silently passes the wrong arguments to your function, your code either crashes with a cryptic `KeyError`/`TypeError` or—worse—executes with bad data and produces incorrect results that look valid on the surface.

## Why this failure is dangerous

The model decides what arguments to pass. It can hallucinate field names, omit required keys, pass a string where you expect an integer, or nest objects incorrectly. The OpenAI API returns `finish_reason: "tool_calls"` regardless of whether the arguments are semantically correct—it only validates JSON syntax, not your schema. If you don't explicitly test argument correctness, malformed calls slip straight into production.

## The exact failure pattern

Your function schema says `user_id` is a required integer. The model returns:

```json
{"user_id": "abc-123", "action": "delete"}
```

Your handler does `int(args["user_id"])` and raises `ValueError`. Or it silently passes `"abc-123"` to a database query that coerces it, deleting nothing and returning no error. Both outcomes are invisible without a test.

## A minimal, runnable test

This test uses the real OpenAI Python SDK, calls the actual API, and asserts that the arguments the model returns conform to your schema—before you ever pass them to your function.

```python
import json
import pytest
from openai import OpenAI

client = OpenAI()  # uses OPENAI_API_KEY from environment

# The schema you register with the model
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "delete_user",
            "description": "Delete a user account by numeric ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "The numeric user ID to delete."
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "Must be true to proceed."
                    }
                },
                "required": ["user_id", "confirm"]
            }
        }
    }
]

def extract_tool_call_args(response, tool_name: str) -> dict:
    """Pull parsed arguments from the first matching tool call."""
    for choice in response.choices:
        if choice.finish_reason == "tool_calls":
            for tc in choice.message.tool_calls:
                if tc.function.name == tool_name:
                    return json.loads(tc.function.arguments)
    raise AssertionError(f"No tool call for '{tool_name}' found in response")

def test_delete_user_args_are_well_formed():
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": "Delete user with ID 42, and confirm the deletion."}
        ],
        tools=TOOLS,
        tool_choice={"type": "function", "function": {"name": "delete_user"}}
    )

    args = extract_tool_call_args(response, "delete_user")

    # Required keys must be present
    assert "user_id" in args, f"Missing 'user_id'. Got: {args}"
    assert "confirm" in args, f"Missing 'confirm'. Got: {args}"

    # Types must match the schema
    assert isinstance(args["user_id"], int), (
        f"'user_id' must be int, got {type(args['user_id']).__name__}: {args['user_id']!r}"
    )
    assert isinstance(args["confirm"], bool), (
        f"'confirm' must be bool, got {type(args['confirm']).__name__}: {args['confirm']!r}"
    )

    # Semantic correctness — the model should pass the right value
    assert args["user_id"] == 42, f"Expected user_id=42, got {args['user_id']}"
    assert args["confirm"] is True, f"Expected confirm=True, got {args['confirm']}"

def test_delete_user_rejects_string_id():
    """Probe the model with an ambiguous prompt to see if it coerces types correctly."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": "Delete the user whose ID is 'user-99'."}
        ],
        tools=TOOLS,
        tool_choice={"type": "function", "function": {"name": "delete_user"}}
    )

    args = extract_tool_call_args(response, "delete_user")

    # The model must not pass a string even when the prompt uses one
    assert isinstance(args["user_id"], int), (
        f"Model passed non-integer user_id: {args['user_id']!r} ({type(args['user_id']).__name__})"
    )
```

Run it with:

```bash
OPENAI_API_KEY=sk-... pytest test_function_calling.py -v
```

## What to assert beyond types

- **No extra keys** — `assert set(args.keys()) <= {"user_id", "confirm"}` catches hallucinated fields that could confuse downstream handlers.
- **Value ranges** — if `user_id` must be positive: `assert args["user_id"] > 0`.
- **Enum values** — if a field is `"status": {"enum": ["active", "inactive"]}`, assert `args["status"] in ("active", "inactive")`.
- **Nested objects** — recurse into sub-dicts and apply the same type checks.

## Why `tool_choice` is essential in tests

Without `tool_choice` forcing a specific function, the model may respond with plain text instead of a tool call, causing your test to raise `AssertionError: No tool call found` rather than testing the argument shape. Force the call explicitly in every test.

---

_Want this as a ready-to-run check across 28 OWASP-Agentic-aligned cases? `pip install "agent-eval-runner[openai]"` then `agent-eval try --model openai:g