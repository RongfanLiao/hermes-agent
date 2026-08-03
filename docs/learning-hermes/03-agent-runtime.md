# Lesson 03 — Trace the Agent Runtime

## Learning goals

After this lesson you should be able to trace a complete turn, identify where
each decision is made, and preserve the loop’s core invariants.

## 1. Two public entry points

`AIAgent` exposes two important interfaces:

- `chat(message)` — convenient call returning final text;
- `run_conversation(...)` — full turn execution returning response, messages,
  and metadata needed by richer surfaces.

Start at [`run_agent.py`](../../run_agent.py), but follow called helpers into
[`agent/`](../../agent/) rather than treating the file as a closed world.

## 2. One turn as a state machine

```text
PREPARE
  resolve runtime, history, prompt, tools, budgets, callbacks
     |
     v
CALL MODEL <------------------------------------------------+
     |                                                       |
     +-- final content --> FINALIZE --> persist/return        |
     |                                                       |
     +-- tool calls --> validate/execute --> append results --+
     |
     +-- retryable error --> backoff/fallback/retry
     |
     +-- interrupt/budget/terminal error --> controlled stop
```

The loop can make several inference calls during one user turn. A “turn” is not
the same as an API request.

## 3. Preparation phase

Preparation combines inputs from several boundaries:

1. **Surface context** — platform, session ID, working directory, callbacks.
2. **History** — prior messages supplied by the surface/session layer.
3. **System prompt** — assembled by prompt-building code and then held stable.
4. **Provider runtime** — provider, model, API mode, base URL, credentials.
5. **Tool definitions** — registry entries filtered through enabled toolsets and
   availability checks.
6. **Budgets** — iteration and context limits, including shared delegation
   budgets.

Read:

- [`agent/prompt_builder.py`](../../agent/prompt_builder.py)
- [`hermes_cli/runtime_provider.py`](../../hermes_cli/runtime_provider.py)
- [`model_tools.py`](../../model_tools.py)
- [`agent/iteration_budget.py`](../../agent/iteration_budget.py)

## 4. Prompt layers

Prompt assembly is ordered because caching and semantics depend on prefix
stability. A useful grouping is:

```text
Stable identity and behavior
  identity, tool-use rules, frozen session-level snapshots

Project/session context
  skills index, context files, platform/session hints

Per-call data
  conversation messages and narrowly scoped runtime additions
```

Do not infer the exact current order from this summary; use
[`agent/prompt_builder.py`](../../agent/prompt_builder.py) and the
[prompt assembly reference](../../website/docs/developer-guide/prompt-assembly.md)
when changing it.

The architectural rule is more durable than the exact list: session-level
prompt material is frozen for the conversation unless an explicit lifecycle
operation, such as compression or reset, rebuilds it.

## 5. Provider resolution and transport

Provider selection is not scattered through each surface. The runtime resolver
maps configuration and credentials into a concrete call strategy.

```text
(requested provider, requested model, config, credentials)
                              |
                              v
                    resolved provider runtime
                  model + api_mode + URL + auth
                              |
                              v
                  transport / protocol adapter
```

The `agent/transports/` package contains protocol-facing transports. Other
adapter modules normalize provider-specific request or response shapes. The
conversation loop should operate on common message and tool-call semantics.

Deep reference:
[Provider runtime resolution](../../website/docs/developer-guide/provider-runtime.md).

## 6. Tool-call cycle

When the model returns tool calls:

1. Preserve the assistant tool-call message.
2. Validate and normalize call arguments.
3. Execute calls sequentially or concurrently according to policy.
4. Capture success or failure as tool-result messages.
5. Append results with correct call IDs and roles.
6. Call the model again with the extended conversation.

The dispatcher boundary is `model_tools.handle_function_call()`. Agent-level
tools may need orchestration context unavailable to a simple standalone
handler, but they still preserve the same model-visible contract.

Read:

- [`agent/tool_executor.py`](../../agent/tool_executor.py)
- [`agent/tool_dispatch_helpers.py`](../../agent/tool_dispatch_helpers.py)
- [`model_tools.py`](../../model_tools.py)
- [Tools runtime](../../website/docs/developer-guide/tools-runtime.md)

## 7. Cross-cutting controls

### Interrupts

Surfaces can request interruption while an inference call or tool sequence is
active. Interruptibility crosses threads, transports, and UI callbacks, so a
fix must cover the real call path rather than only a button handler.

### Iteration budget

Tool-calling iterations are bounded. Delegation may share a budget so child
agents cannot multiply work without bound. A limited grace call can let the
model summarize after the normal budget is exhausted.

### Retries and fallback

Errors are classified. Retryable failures may back off; supported failures may
switch to a fallback runtime. The agent loop owns retry semantics, while the
transport owns protocol mechanics.

### Compression

When context pressure becomes high, the context engine reduces history while
preserving a coherent conversation and session lineage. Compression is a
lifecycle operation, not arbitrary message deletion.

### Callbacks

The core reports tool start/progress/completion, streaming text, approvals,
clarification requests, and other events through callbacks. Surfaces decide how
to render or transport those events.

## 8. Invariants to protect

Any loop change should preserve:

- one stable system prompt per conversation lifecycle;
- valid message roles and tool-call/result pairing;
- no synthetic user injection in the middle of model/tool alternation;
- bounded iteration and delegation;
- interrupt checks at potentially long-running boundaries;
- tool errors represented to the model without crashing the whole process when
  recoverable;
- exactly one finalization path for persistence/accounting semantics;
- surface-neutral core behavior.

## Code walk

```bash
rg -n "^class AIAgent|def run_conversation|def chat" run_agent.py
rg -n "iteration_budget|_budget_grace_call|interrupt" run_agent.py agent
rg -n "handle_function_call|tool_calls|tool_call_id" run_agent.py agent model_tools.py
rg -n "build.*prompt|system_prompt" agent/prompt_builder.py run_agent.py
rg -n "finaliz" run_agent.py agent/turn_finalizer.py
```

Read only enough surrounding code to draw the call graph. Then confirm behavior
against tests under `tests/run_agent/`, `tests/agent/`, and `tests/conformance/`.

## Exercise: produce a turn trace

Create a trace table for a prompt that causes `read_file` and then returns an
answer:

| Step | Owner | Input | Output | Persistent? |
|---|---|---|---|---|
| 1 | surface | user text | normalized turn request | maybe |
| 2 | agent | history + prompt + tools | model request | no |
| 3 | transport | request | assistant tool call | no |
| 4 | dispatcher | name + args | tool result | no |
| 5 | agent | appended tool result | next model request | no |
| 6 | finalizer/surface | final text + metadata | display + stored messages | yes |

Add the exact functions you find beside each row.

## Checkpoint

- Why can one turn contain multiple model calls?
- Which layer chooses a fallback and which layer speaks the provider protocol?
- Why must a tool result retain its tool-call identity?
- When is changing conversation history architecturally legitimate?
