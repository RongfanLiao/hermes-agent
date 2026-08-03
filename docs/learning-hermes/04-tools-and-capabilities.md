# Lesson 04 — Tools and Capabilities

## Learning goals

After this lesson you should understand the complete path from a tool module to
a model-visible schema, know the difference between tools and toolsets, and be
able to choose a lower-footprint extension when appropriate.

## 1. Four distinct concepts

| Concept | Purpose |
|---|---|
| Tool schema | Tells the model the tool name, purpose, and argument contract |
| Tool handler | Performs the action and returns a result |
| Tool registry entry | Binds schema, handler, group, availability, and metadata |
| Toolset | Names a selectable group of tool names |

Confusing these produces duplicated lists and inconsistent behavior.

## 2. Registration and discovery

Built-in tool modules call `registry.register(...)` at module scope. Discovery
scans tool files, imports self-registering modules, and lets registration build
the runtime catalog.

```text
tools/example_tool.py
  schema + handler + check_fn
            |
            | registry.register(...)
            v
tools/registry.py catalog
            |
            | queried by model_tools.py
            v
filtered model-visible definitions + executable dispatch
```

The registry is intentionally low in the dependency graph. It does not import
every tool implementation.

## 3. Availability is separate from enablement

A tool can be absent for several different reasons:

1. Its module was not discovered or a plugin was not loaded.
2. Its toolset is not enabled for the current surface/profile.
3. The tool is explicitly disabled.
4. Its `check_fn` says a prerequisite is unavailable.
5. Required credentials or environment bridging are missing.
6. A surface-specific safety policy removes it.

This distinction matters when debugging “the model cannot see tool X.” Check
the chain in that order instead of editing the core tool list immediately.

`check_fn` is especially important: it keeps service-specific schemas out of
turns where that service is not configured.

## 4. Toolset resolution

[`toolsets.py`](../../toolsets.py) groups names and composes groups. Surfaces
select toolsets based on configuration and trust level. For example, webhook
input can receive a deliberately constrained set because its content may be
untrusted.

Toolsets answer “which registered tools are eligible?” They do not load code,
execute handlers, or prove that prerequisites are healthy.

## 5. Dispatch path

```text
model tool_call
  name + JSON arguments + call ID
        |
        v
agent tool executor
  concurrency, callbacks, cancellation, agent-level context
        |
        v
model_tools.handle_function_call
  lookup, argument handling, async bridge, error wrapping
        |
        v
registered handler
        |
        v
serialized tool result -> assistant's next model call
```

Handlers should return a stable, model-readable result. Exceptions that are
normal operational outcomes should generally become explicit error results;
process-corrupting or cancellation conditions need separate handling.

## 6. Safety boundary

Tool execution is where model output becomes a side effect. The path can
include:

- argument validation;
- dangerous-command detection;
- user approval;
- path and media-delivery restrictions;
- environment isolation;
- credential scoping;
- result truncation and redaction;
- timeout and cancellation;
- surface-specific tool filtering.

Do not “secure” a capability by disabling its intended use. Trace the original
feature contract and place the narrowest guard at the boundary where untrusted
data becomes authority.

## 7. Execution environments

The terminal tool is a stable model-facing capability backed by several
environments under [`tools/environments/`](../../tools/environments/). This is
an adapter boundary:

```text
terminal tool contract
        |
        +-- local
        +-- Docker
        +-- SSH
        +-- Daytona
        +-- Modal
        +-- Singularity
        +-- other configured backends
```

Fix backend-specific behavior in the backend. Fix contract-wide behavior in
the terminal orchestration. Avoid exposing one core tool per backend.

## 8. Capability footprint ladder

Before adding a tool, choose the smallest permanent surface:

1. Extend existing code or an existing tool.
2. Add a CLI command plus a skill for procedural use.
3. Add a service-gated tool with a `check_fn`.
4. Add a standalone plugin for niche or third-party capability.
5. Add an MCP server and catalog entry for structured external tools.
6. Add a new core tool only if it is broadly fundamental and cannot be
   expressed through existing terminal/file/MCP surfaces.

Every core schema is sent repeatedly, so the cost is behavioral, cognitive,
and monetary—not just code size.

## Code walk

Pick one simple tool, such as a file tool, and trace it:

```bash
rg -n "registry.register\(" tools/file_tools.py
rg -n "def register|def get_definitions|def dispatch" tools/registry.py
rg -n "def get_tool_definitions|def handle_function_call" model_tools.py
rg -n '"file"|read_file' toolsets.py
rg -n "read_file" tests/tools tests/run_agent
```

Then inspect one service-gated tool and one terminal backend. Compare which
layer changes and which contracts stay fixed.

## Debugging decision tree

```text
Tool missing from model schema?
  Is module/plugin discovered?
    no -> discovery/manifest/import issue
    yes
  Is its toolset enabled and not disabled?
    no -> configuration/surface policy
    yes
  Does check_fn pass?
    no -> prerequisite/credential/backend health
    yes -> inspect definition filtering and refresh lifecycle

Tool visible but call fails?
  Validate arguments -> registry lookup -> handler -> backend -> result bridge
```

## Exercises

1. Find a tool gated by `check_fn` and list every prerequisite it probes.
2. Find where maximum result size is applied.
3. Compare a core tool with a plugin-provided tool.
4. Design a Git issue integration and justify which footprint rung it belongs
   on.

## Checkpoint

- What does the registry own that a toolset does not?
- Why can a registered tool still be invisible?
- Where should backend-specific terminal code live?
- Why is a new core tool the last rung?
