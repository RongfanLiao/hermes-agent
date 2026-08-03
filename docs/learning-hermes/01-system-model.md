# Lesson 01 — Build the System Model

## Learning goals

After this lesson you should be able to explain Hermes without naming every
file, identify its major domain objects, and distinguish the stable core from
the replaceable edges.

## 1. Hermes is an agent runtime, not a chat application

A chat application sends text to a model and displays text back. Hermes is a
long-lived agent runtime that also:

- assembles a stable system prompt and conversation context;
- selects credentials and a provider transport;
- advertises available actions as tool schemas;
- executes tool calls, feeds results back, and repeats;
- persists and resumes sessions;
- receives work from several interfaces;
- schedules autonomous work;
- learns through memory and skills;
- extends through plugins, providers, adapters, and MCP.

The conversational engine is reused. The CLI, gateway, TUI, desktop app, ACP,
cron, and batch runner are not independent agent implementations.

## 2. Four planes

A useful mental model is to divide the system into four planes. These are
conceptual boundaries, not necessarily directories.

```text
Interaction plane   CLI, TUI, desktop, messaging platforms, ACP, API
       |
Control plane       conversation loop, budgets, retries, interrupts, routing
       |
Capability plane    tools, terminal backends, MCP, skills, plugins
       |
State plane         session DB, config, memory, files, credentials, job store
```

### Interaction plane

Owns protocol and presentation concerns: input, output, streaming, message
formatting, approvals, media, slash-command UX, and lifecycle events.

Representative code:

- [`cli.py`](../../cli.py) — classic interactive CLI orchestration
- [`ui-tui/`](../../ui-tui/) — Ink terminal UI
- [`tui_gateway/server.py`](../../tui_gateway/server.py) — JSON-RPC backend for
  TUI, dashboard, and desktop clients
- [`gateway/`](../../gateway/) — messaging gateway and platform adapters
- [`acp_adapter/`](../../acp_adapter/) — editor integration

### Control plane

Owns the agent turn: prompt construction, inference calls, tool-loop decisions,
budgets, fallback, compression triggers, callbacks, and finalization.

Representative code:

- [`run_agent.py`](../../run_agent.py) — `AIAgent`, the main orchestrator
- [`agent/conversation_loop.py`](../../agent/conversation_loop.py) — extracted
  loop helpers
- [`agent/chat_completion_helpers.py`](../../agent/chat_completion_helpers.py)
- [`agent/turn_finalizer.py`](../../agent/turn_finalizer.py)
- [`agent/iteration_budget.py`](../../agent/iteration_budget.py)

### Capability plane

Owns actions and integrations. The core should know a contract, not every
backend detail.

Representative code:

- [`tools/registry.py`](../../tools/registry.py) — tool metadata and discovery
- [`model_tools.py`](../../model_tools.py) — schema collection and dispatch
- [`toolsets.py`](../../toolsets.py) — named capability groupings
- [`tools/environments/`](../../tools/environments/) — execution backends
- [`hermes_cli/plugins.py`](../../hermes_cli/plugins.py) — plugin lifecycle

### State plane

Owns durable or scoped data. Different kinds of state intentionally have
different lifetimes.

Representative code:

- [`hermes_state.py`](../../hermes_state.py) — SQLite session database and FTS
- [`gateway/session.py`](../../gateway/session.py) — gateway session store
- [`hermes_constants.py`](../../hermes_constants.py) — profile-aware paths
- [`agent/memory_manager.py`](../../agent/memory_manager.py) — memory orchestration
- [`cron/jobs.py`](../../cron/jobs.py) — scheduled job records

## 3. Domain model

You can understand most code by tracking these objects:

| Object | Meaning | Typical owner |
|---|---|---|
| Conversation | A logical dialogue over time | surface/session layer |
| Turn | One user request plus all model/tool iterations until a final answer | `AIAgent` |
| Message | A role-tagged unit: system, user, assistant, or tool | agent + session store |
| Session | Persistent identity, metadata, history, and lineage for a conversation | `SessionDB` / surface store |
| Agent | Runtime configured to execute turns | `AIAgent` |
| Tool definition | Name, JSON schema, grouping, availability, and handler | tool registry |
| Tool call | A model-requested invocation with arguments and call ID | agent loop / dispatcher |
| Provider runtime | Model, API mode, endpoint, credentials, and routing policy | runtime resolver |
| Event | Surface-neutral inbound or outbound occurrence | gateway or JSON-RPC bridge |
| Job | A scheduled prompt with execution and delivery policy | cron subsystem |
| Skill | Instructional content loaded when needed | skills subsystem |
| Plugin | Discoverable package that registers capabilities or hooks | plugin manager |

Do not collapse these concepts. In particular, an `AIAgent` is not a session,
a session is not just a list of messages, and a toolset is not a tool registry.

## 4. Narrow waist and wide edges

Hermes deliberately keeps the center small in concept even where central files
are large in line count.

```text
many inputs      ->   conversation contract   -> many capabilities
many providers   ->   model-call contract     -> many transports
many tools       ->   registry contract       -> many implementations
many platforms   ->   MessageEvent contract   -> many adapters
```

This is the “narrow waist” principle. Adding a core model tool or mutating the
system prompt affects every turn. Adding a plugin, skill, provider backend, or
platform adapter affects only users who select it.

## 5. Two non-negotiable invariants

### Prompt-prefix stability

Past context and the system prompt form a cacheable prefix. Rebuilding or
mutating that prefix mid-conversation increases cost and can change behavior.
Context compression is the deliberate exception.

### Message-role alternation

Model APIs expect a coherent sequence of user, assistant, and tool messages.
Synthetic user messages inserted inside the tool loop or consecutive messages
with the same semantic role can break provider behavior.

These are architecture constraints, not optimizations to clean up later.

## Code walk

Run these searches and inspect only the surrounding blocks:

```bash
rg -n "^class AIAgent|def run_conversation|def chat" run_agent.py
rg -n "^class SessionDB|^class SessionStore" hermes_state.py gateway/session.py
rg -n "^class MessageEvent|^class BasePlatformAdapter" gateway/platforms/base.py
rg -n "^class ToolEntry|def register|def get_definitions" tools/registry.py
rg -n "def resolve_runtime_provider" hermes_cli/runtime_provider.py
```

Then compare this mental model with the project’s
[architecture overview](../../website/docs/developer-guide/architecture.md).

## Separation-point checklist

When reading a function, ask:

1. Is this translating an external protocol or deciding agent behavior?
2. Is this selecting policy or implementing a backend mechanism?
3. Is this transient turn state or durable session state?
4. Is this universal behavior or an optional capability?
5. Could this dependency point outward through an interface instead?

## Exercises

1. Trace one user message from `hermes` entry point to `AIAgent.chat()`.
2. Find one `MessageEvent` producer and one consumer.
3. Pick a tool and identify its definition, availability check, handler, and
   toolset.
4. Explain why a new weather integration should normally be a skill, plugin,
   or MCP server rather than a new core tool.

## Checkpoint

You are ready for lesson 2 if you can answer:

- Which plane owns model/tool iteration?
- Why is `tui_gateway` not the agent core?
- What is the difference between a tool definition and a toolset?
- Which two invariants constrain changes to message history and prompts?
