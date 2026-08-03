# Lesson 09 — Code Atlas and Reading Reference

Use this file as a lookup table after completing the earlier lessons. File
locations are current references, while contracts and ownership rules are the
more durable knowledge.

## 1. Process entry points

| Entry | File | Responsibility |
|---|---|---|
| `hermes` console script | [`hermes_cli/main.py`](../../hermes_cli/main.py) | top-level command parsing and routing |
| Classic interactive chat | [`cli.py`](../../cli.py) | prompt_toolkit/Rich surface and `HermesCLI` |
| Direct agent runner | [`run_agent.py`](../../run_agent.py) | `AIAgent` and direct execution entry |
| Messaging gateway | [`gateway/run.py`](../../gateway/run.py) | long-running platform/session orchestrator |
| TUI gateway | [`tui_gateway/entry.py`](../../tui_gateway/entry.py) | JSON-RPC process entry |
| TUI RPC implementation | [`tui_gateway/server.py`](../../tui_gateway/server.py) | methods, events, live UI sessions |
| ACP | [`acp_adapter/entry.py`](../../acp_adapter/entry.py) | editor protocol entry |
| Batch generation | [`batch_runner.py`](../../batch_runner.py) | controlled parallel agent runs |

## 2. Agent runtime modules

| Concern | Primary module(s) | Boundary |
|---|---|---|
| Agent orchestration | [`run_agent.py`](../../run_agent.py) | sequences the whole turn |
| Loop helpers | [`agent/conversation_loop.py`](../../agent/conversation_loop.py) | extracted loop operations |
| Model-call helpers | [`agent/chat_completion_helpers.py`](../../agent/chat_completion_helpers.py) | call construction/handling |
| Prompt assembly | [`agent/prompt_builder.py`](../../agent/prompt_builder.py), [`agent/system_prompt.py`](../../agent/system_prompt.py) | stable behavior/context prefix |
| Prompt caching | [`agent/prompt_caching.py`](../../agent/prompt_caching.py) | provider cache semantics |
| Message shape/safety | [`agent/message_content.py`](../../agent/message_content.py), [`agent/message_sanitization.py`](../../agent/message_sanitization.py) | canonical content and cleanup |
| Tool execution | [`agent/tool_executor.py`](../../agent/tool_executor.py) | call scheduling and callbacks |
| Tool guardrails | [`agent/tool_guardrails.py`](../../agent/tool_guardrails.py) | execution policy |
| Iteration budget | [`agent/iteration_budget.py`](../../agent/iteration_budget.py) | bounded agent/delegation work |
| Turn finalization | [`agent/turn_finalizer.py`](../../agent/turn_finalizer.py) | final response/accounting path |
| Error classification | [`agent/error_classifier.py`](../../agent/error_classifier.py) | retry/fallback-relevant classes |
| Context engine | [`agent/context_engine.py`](../../agent/context_engine.py) | compression strategy contract |
| Default compression | [`agent/context_compressor.py`](../../agent/context_compressor.py) | default lossy reduction |
| Memory contract | [`agent/memory_provider.py`](../../agent/memory_provider.py) | cross-session backend API |
| Memory orchestration | [`agent/memory_manager.py`](../../agent/memory_manager.py) | memory lifecycle/policy |
| Subagent lifecycle | [`agent/subagent_lifecycle.py`](../../agent/subagent_lifecycle.py) | parent/child events and state |
| Trajectories | [`agent/trajectory.py`](../../agent/trajectory.py) | training/replay output |

## 3. Provider and transport modules

| Concern | Primary module(s) |
|---|---|
| Shared runtime resolution | [`hermes_cli/runtime_provider.py`](../../hermes_cli/runtime_provider.py) |
| Provider auth/catalog | [`hermes_cli/auth.py`](../../hermes_cli/auth.py), [`hermes_cli/provider_catalog.py`](../../hermes_cli/provider_catalog.py) |
| Model catalog/metadata | [`hermes_cli/models.py`](../../hermes_cli/models.py), [`agent/model_metadata.py`](../../agent/model_metadata.py) |
| Runtime transports | [`agent/transports/`](../../agent/transports/) |
| Provider protocol adapters | `agent/*_adapter.py` |
| Credential pools/sources | [`agent/credential_pool.py`](../../agent/credential_pool.py), [`agent/credential_sources.py`](../../agent/credential_sources.py) |
| Provider plugin base | [`providers/base.py`](../../providers/base.py) |
| Model-provider plugins | [`plugins/model-providers/`](../../plugins/model-providers/) |

Read [provider runtime](../../website/docs/developer-guide/provider-runtime.md)
before changing precedence or credentials.

## 4. Tools and execution

| Concern | Primary module(s) |
|---|---|
| Registry/discovery | [`tools/registry.py`](../../tools/registry.py) |
| Definition filtering/dispatch | [`model_tools.py`](../../model_tools.py) |
| Toolset policy | [`toolsets.py`](../../toolsets.py) |
| File operations | [`tools/file_tools.py`](../../tools/file_tools.py) |
| Terminal orchestration | [`tools/terminal_tool.py`](../../tools/terminal_tool.py) |
| Terminal backends | [`tools/environments/`](../../tools/environments/) |
| Command approval | [`tools/approval.py`](../../tools/approval.py) |
| Background processes | [`tools/process_registry.py`](../../tools/process_registry.py) |
| Delegation | [`tools/delegate_tool.py`](../../tools/delegate_tool.py) |
| MCP | [`tools/mcp_tool.py`](../../tools/mcp_tool.py) |
| Lazy dependencies | [`tools/lazy_deps.py`](../../tools/lazy_deps.py) |

## 5. State and configuration

| Concern | Primary module(s) |
|---|---|
| Session DB and FTS | [`hermes_state.py`](../../hermes_state.py) |
| Profile-aware paths | [`hermes_constants.py`](../../hermes_constants.py) |
| Config model/defaults | [`hermes_cli/config.py`](../../hermes_cli/config.py), [`hermes_cli/config_defaults.py`](../../hermes_cli/config_defaults.py) |
| Config migration | [`hermes_cli/config_migrations.py`](../../hermes_cli/config_migrations.py) |
| Gateway session mapping | [`gateway/session.py`](../../gateway/session.py) |
| Cron records | [`cron/jobs.py`](../../cron/jobs.py) |
| Cron execution | [`cron/scheduler.py`](../../cron/scheduler.py) |
| Logging | [`hermes_logging.py`](../../hermes_logging.py) |

## 6. Surface modules

### Classic CLI

| Concern | File |
|---|---|
| Interactive orchestrator | [`cli.py`](../../cli.py) |
| Process commands | [`hermes_cli/main.py`](../../hermes_cli/main.py) and [`hermes_cli/subcommands/`](../../hermes_cli/subcommands/) |
| Slash-command definitions | [`hermes_cli/commands.py`](../../hermes_cli/commands.py) |
| CLI callbacks/approvals | [`hermes_cli/callbacks.py`](../../hermes_cli/callbacks.py) |
| Model switching | [`hermes_cli/model_switch.py`](../../hermes_cli/model_switch.py) |
| Setup | [`hermes_cli/setup.py`](../../hermes_cli/setup.py) |

### Messaging gateway

| Concern | File |
|---|---|
| Orchestrator | [`gateway/run.py`](../../gateway/run.py) |
| Adapter/event contracts | [`gateway/platforms/base.py`](../../gateway/platforms/base.py) |
| Built-in adapters | [`gateway/platforms/`](../../gateway/platforms/) |
| Platform plugins | [`plugins/platforms/`](../../plugins/platforms/) |
| Delivery | [`gateway/delivery.py`](../../gateway/delivery.py) |
| Authorization/pairing | [`gateway/authz_mixin.py`](../../gateway/authz_mixin.py), [`gateway/pairing.py`](../../gateway/pairing.py) |
| Slash dispatch | [`gateway/slash_commands.py`](../../gateway/slash_commands.py) |
| Hooks | [`gateway/hooks.py`](../../gateway/hooks.py) |

### TUI, dashboard, and desktop

| Concern | File/directory |
|---|---|
| Ink app | [`ui-tui/src/`](../../ui-tui/src/) |
| JSON-RPC backend | [`tui_gateway/server.py`](../../tui_gateway/server.py) |
| Dashboard PTY | [`hermes_cli/pty_bridge.py`](../../hermes_cli/pty_bridge.py) |
| Dashboard web UI | [`web/src/`](../../web/src/) |
| Shared web/desktop transport | [`apps/shared/`](../../apps/shared/) |
| Electron desktop | [`apps/desktop/`](../../apps/desktop/) |

## 7. Extension modules

| Extension | Contract/discovery | Implementations |
|---|---|---|
| General plugins | [`hermes_cli/plugins.py`](../../hermes_cli/plugins.py) | [`plugins/`](../../plugins/) and external repos |
| Skills | `agent/skill_*.py` | [`skills/`](../../skills/), [`optional-skills/`](../../optional-skills/) |
| MCP | [`tools/mcp_tool.py`](../../tools/mcp_tool.py) | external servers / catalog |
| Memory providers | [`agent/memory_provider.py`](../../agent/memory_provider.py) | [`plugins/memory/`](../../plugins/memory/) |
| Context engines | [`agent/context_engine.py`](../../agent/context_engine.py) | [`plugins/context_engine/`](../../plugins/context_engine/) |
| Platform adapters | [`gateway/platforms/base.py`](../../gateway/platforms/base.py) | built-in and plugin adapters |
| Media/search providers | `agent/*_provider.py`, `agent/*_registry.py` | provider plugins |

## 8. Test atlas

| Change area | First places to inspect |
|---|---|
| Agent turn/message semantics | `tests/run_agent/`, `tests/agent/`, `tests/conformance/` |
| Tools | `tests/tools/` |
| CLI | `tests/cli/`, `tests/hermes_cli/` |
| Gateway/platforms | `tests/gateway/` |
| Session database | `tests/hermes_state/`, `tests/state/` |
| TUI gateway | `tests/tui_gateway/` |
| TUI TypeScript | `ui-tui/src/**/*.test.*` |
| Desktop | `apps/desktop/src/**/*.test.*`, `apps/desktop/e2e/` |
| ACP | `tests/acp/`, `tests/acp_adapter/` |
| Cron | `tests/cron/` |
| Plugins | `tests/plugins/` and provider-specific suites |
| End-to-end boundaries | `tests/e2e/`, `tests/integration/` |

The general Python test runner is:

```bash
scripts/run_tests.sh
```

For focused work, pass the relevant pytest path or use the package-specific
commands documented in `AGENTS.md` files and local READMEs.

## 9. Fast concept lookup

| If you are asking… | Start with… |
|---|---|
| Why did the model see this instruction? | prompt builder and context files |
| Why did it call this provider? | runtime-provider precedence |
| Why can’t it see a tool? | discovery → toolset → `check_fn` |
| Why did a gateway message reach this session? | session-key routing and guards |
| Why did resume lose or duplicate a message? | live/durable reconciliation and lineage |
| Why is desktop behavior different from TUI? | separate clients over shared RPC backend |
| Where should an integration live? | [extension seams](07-extension-seams.md) |
| How should I prove a fix? | [change playbook](08-change-playbook.md) |

## 10. Final mastery exercise

Choose one vertical slice—`/model`, `read_file`, session resume, a gateway
message, or a cron run—and produce a one-page architecture note containing:

1. the initiating surface and input contract;
2. the application orchestrator;
3. every policy decision;
4. every adapter/mechanism boundary;
5. transient and durable state changes;
6. callbacks/events emitted;
7. failure and cancellation paths;
8. the tests proving the slice.

If you can do this without reading a god-file top to bottom, you understand the
project’s separation points well enough to make focused contributions.
