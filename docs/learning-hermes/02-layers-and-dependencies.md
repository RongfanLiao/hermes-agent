# Lesson 02 — Layers and Dependency Direction

## Learning goals

After this lesson you should be able to place a module in the architecture,
recognize an improper dependency, and choose a separation point for new code.

## 1. The practical layer stack

Hermes is not organized as a textbook layered application. Some large files
coordinate multiple subsystems. The dependency direction is still readable:

```text
Layer 6  Product surfaces
         cli.py, gateway/, ui-tui/, apps/desktop/, acp_adapter/, batch_runner.py
                                |
Layer 5  Application orchestration
         AIAgent, GatewayRunner, TUI RPC session orchestration, cron scheduler
                                |
Layer 4  Policies and use cases
         prompt building, routing, compression, approval, delivery, lifecycle
                                |
Layer 3  Contracts and registries
         tool registry, provider ABCs, platform adapter ABC, plugin context
                                |
Layer 2  Mechanisms and adapters
         model transports, tool handlers, terminal backends, platform clients
                                |
Layer 1  State and utilities
         SQLite, config/path helpers, atomic files, redaction, serialization
```

Higher layers may coordinate lower layers. Lower layers should not import a UI
or product surface merely to get shared behavior.

## 2. The load-bearing import chain

The clearest explicit dependency chain is the tool system:

```text
tools/registry.py
       ^
tools/*.py                 registration at import time
       ^
model_tools.py             discovery, schema collection, dispatch
       ^
run_agent.py and surfaces  use tools through the common runtime
```

[`tools/registry.py`](../../tools/registry.py) stays independent of tool
implementations and `model_tools.py` to avoid circular imports. Tool modules
self-register. `model_tools.py` discovers them. Product surfaces do not need a
manual list of every implementation.

This pattern repeats elsewhere:

- contract → implementation registry → orchestrator;
- event/data shape → adapter → surface runner;
- provider ABC → provider plugin → selecting runtime;
- state API → persistence implementation → use case.

## 3. Separate policy from mechanism

Policy answers “what should happen?” Mechanism answers “how is it done?”

| Policy | Mechanism |
|---|---|
| Which toolsets are enabled? | How `terminal` runs a command |
| Whether approval is required | How the approval prompt is rendered |
| Which provider/model wins | How Anthropic or OpenAI HTTP is called |
| When context is compressed | How the summary is generated |
| Where a gateway reply goes | How Telegram or Slack sends it |
| Which job is due | How its result is delivered |

A common coupling bug is putting product policy in a backend implementation,
or importing a mechanism directly from every surface instead of centralizing
the policy once.

## 4. Separate orchestration from computation

Large orchestrators are expected to sequence behavior, but reusable or
testable logic should live in focused modules.

Examples:

- [`run_agent.py`](../../run_agent.py) coordinates a turn, while modules under
  [`agent/`](../../agent/) implement message sanitation, provider transports,
  prompt caching, tool execution, and finalization.
- [`gateway/run.py`](../../gateway/run.py) coordinates sessions and platform
  events, while `gateway/delivery.py`, `gateway/pairing.py`, `gateway/hooks.py`,
  and adapter modules own focused mechanisms.
- [`cli.py`](../../cli.py) coordinates the classic CLI, while
  [`hermes_cli/`](../../hermes_cli/) owns configuration, slash-command
  definitions, provider resolution, setup, plugins, and subcommands.

When a feature makes an orchestrator longer, first ask whether it is a new
sequence in that orchestrator or a reusable policy/mechanism that deserves a
module.

## 5. Seven important separation points

### A. Entry point / use case

`hermes_cli.main:main` parses process-level intent. Interactive chat, gateway,
setup, and cron are different use cases. Do not put agent-loop behavior in the
argument parser.

### B. Surface / conversation engine

Surfaces own presentation and protocol. They instantiate and configure
`AIAgent`, pass callbacks, and persist/display results. They should not fork the
model/tool loop.

### C. Conversation engine / provider transport

The agent loop owns retries and iteration semantics. Runtime resolution and
transport adapters own credentials, endpoint shape, and protocol conversion.

### D. Model-visible schema / tool implementation

The model sees a JSON schema. Dispatch resolves that name to a handler. The
handler should not care whether the call originated in CLI, gateway, or ACP.

### E. Session / memory

Session history recreates a conversation. Memory preserves selected knowledge
across conversations. Treating all history as memory bloats prompts and breaks
lifecycle expectations.

### F. Configuration / secrets

Behavioral settings belong in profile-aware `config.yaml`. Credentials belong
in secret storage or `.env`. A backend may receive bridged environment values,
but that is not the user-facing configuration model.

### G. Core / extension

Optional integrations belong behind skills, plugins, MCP, ABCs, hooks, or
`check_fn` gating. Core schemas and prompts are global cost surfaces.

## 6. Dependency smells

Watch for:

- a tool importing `cli.py` to render output;
- a platform adapter constructing provider credentials itself;
- multiple surfaces maintaining separate lists of slash-command aliases;
- a storage module importing gateway or desktop code;
- a plugin editing core files for its own special case;
- a model transport deciding UI wording;
- a feature reading a new non-secret `HERMES_*` variable instead of config;
- duplicated model/tool loops in a UI.

## Code walk

```bash
# The process entry point and command routing
rg -n "hermes =|def main" pyproject.toml hermes_cli/main.py

# Central slash-command source of truth
rg -n "COMMAND_REGISTRY|def resolve_command" hermes_cli/commands.py

# Contract/implementation pairs
rg -n "class ContextEngine|class MemoryProvider" agent
rg -n "class BasePlatformAdapter" gateway/platforms/base.py
rg -n "class .*Transport" agent/transports

# Tool dependency chain
sed -n '1,80p' tools/registry.py
rg -n "discover_builtin_tools|get_tool_definitions|handle_function_call" model_tools.py
```

## Exercises

For each proposed change, name its layer and separation point:

1. Add a new Slack message formatting rule.
2. Add retry classification shared by every provider transport.
3. Add a niche project-management integration.
4. Add an FTS query used by CLI and desktop.
5. Add a new slash-command alias.

Suggested answers: platform adapter/delivery; agent policy helper; plugin or MCP;
state API; central command registry.

## Checkpoint

- Can you explain why imports should generally point from surfaces toward
  contracts and mechanisms?
- Can you distinguish policy, mechanism, and orchestration in a feature?
- Can you name the seven separation points without referring to directories?
