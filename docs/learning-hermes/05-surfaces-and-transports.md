# Lesson 05 — Surfaces, Transports, and Adapters

## Learning goals

After this lesson you should know which UI/runtime owns which concerns, how
events reach the shared agent, and where to implement a surface-specific
feature.

## 1. Surface comparison

| Surface | Front end | Backend/orchestrator | Connection to agent |
|---|---|---|---|
| Classic CLI | prompt_toolkit + Rich | `HermesCLI` in `cli.py` | direct in-process calls |
| Ink TUI | TypeScript/Ink in `ui-tui/` | `tui_gateway` Python process | stdio JSON-RPC |
| Dashboard chat | browser xterm embedding real TUI | PTY bridge + TUI gateway | embedded `hermes --tui` |
| Desktop | Electron + React | headless `hermes serve` / `tui_gateway` | WebSocket JSON-RPC |
| Messaging | Telegram, Slack, Discord, etc. | `GatewayRunner` | adapter events + in-process agent |
| ACP | editor ACP client | `HermesACPAgent` | ACP protocol mapped to agent callbacks |
| Cron | no interactive UI | scheduler | creates isolated agent runs |
| Batch | batch caller | batch runner | creates controlled agent runs |

The desktop app is a separate chat surface. The dashboard’s primary chat is
not: it embeds the real TUI through a PTY.

## 2. The surface contract

Every interactive surface performs some version of:

1. normalize user or protocol input;
2. resolve conversation/session identity;
3. load or initialize session state;
4. configure an `AIAgent` and callbacks;
5. submit the turn;
6. project stream/tool/approval events into its protocol;
7. persist state and deliver final output.

The shape differs, but the conversational semantics should converge at the
agent boundary.

## 3. Classic CLI

[`hermes_cli/main.py`](../../hermes_cli/main.py) is the process-level command
router. Interactive chat flows into [`cli.py`](../../cli.py), which owns classic
terminal concerns such as input, display, spinner behavior, slash-command
dispatch, and session UX.

Put code here when it only concerns the classic terminal interface. Put shared
slash-command metadata in
[`hermes_cli/commands.py`](../../hermes_cli/commands.py), the central registry
used by several surfaces.

## 4. TUI, dashboard, and desktop

[`tui_gateway/server.py`](../../tui_gateway/server.py) exposes JSON-RPC methods
and emits events for sessions, prompts, tools, approvals, configuration, and
other structured UI needs.

```text
Ink TUI --stdio JSON-RPC--+
                          |
Desktop --WebSocket RPC---+--> tui_gateway --> AIAgent/session services
```

The dashboard chat embeds the Ink TUI via
[`hermes_cli/pty_bridge.py`](../../hermes_cli/pty_bridge.py). Therefore, primary
transcript or composer features intended for both terminal TUI and dashboard
belong in `ui-tui`, not in a second React chat implementation.

Desktop architecture has its own scoped guide:
[`apps/desktop/AGENTS.md`](../../apps/desktop/AGENTS.md) and
[`apps/desktop/DESIGN.md`](../../apps/desktop/DESIGN.md).

## 5. Messaging gateway

Platform adapters translate third-party events into a common
`MessageEvent`. `GatewayRunner` handles authorization, session routing,
running-turn guards, agent creation, and delivery orchestration.

```text
platform SDK/webhook
       |
BasePlatformAdapter implementation
       |
MessageEvent
       |
GatewayRunner: auth -> session -> command/turn -> delivery
       |
AIAgent + callbacks
```

Important modules:

- [`gateway/platforms/base.py`](../../gateway/platforms/base.py) — event and
  adapter contracts plus shared media behavior
- [`gateway/run.py`](../../gateway/run.py) — gateway orchestration
- [`gateway/session.py`](../../gateway/session.py) — session mapping/storage
- [`gateway/delivery.py`](../../gateway/delivery.py) — outbound delivery
- [`gateway/pairing.py`](../../gateway/pairing.py) — DM authorization
- [`gateway/hooks.py`](../../gateway/hooks.py) — lifecycle extension events

Use the [gateway internals reference](../../website/docs/developer-guide/gateway-internals.md)
for the detailed flow.

## 6. ACP

ACP maps editor-native sessions, content blocks, permissions, cancellation,
and tool rendering to the shared Hermes runtime. ACP protocol behavior belongs
in [`acp_adapter/`](../../acp_adapter/); general conversation behavior does not.

Read [ACP internals](../../website/docs/developer-guide/acp-internals.md).

## 7. Slash commands as a separation example

Slash commands demonstrate correct ownership:

- [`hermes_cli/commands.py`](../../hermes_cli/commands.py) owns canonical names,
  aliases, descriptions, categories, and surface flags.
- Classic CLI and gateway own their dispatch handlers.
- TUI and desktop curate client-owned commands, then fall through to backend
  execution.
- Skill and quick commands are extensions surfaced by backend catalogs.

Adding an alias should change the registry once, not every platform menu.

## 8. Where should a UI change go?

| Desired behavior | Correct home |
|---|---|
| Change model/tool-loop semantics everywhere | agent core/helper |
| Change classic CLI rendering only | `cli.py` / `agent/display.py` as appropriate |
| Change TUI and dashboard transcript/composer | `ui-tui/` |
| Change desktop-only panels or composer | `apps/desktop/` |
| Add structured RPC state used by TUI/desktop | `tui_gateway/` plus clients |
| Change one messaging platform’s formatting | its platform adapter |
| Change shared outbound gateway delivery | `gateway/delivery.py` or common gateway layer |
| Add slash metadata/alias | central command registry |

## Code walk

```bash
rg -n "def main" hermes_cli/main.py cli.py tui_gateway/entry.py gateway/run.py
rg -n "class MessageEvent|class BasePlatformAdapter" gateway/platforms/base.py
rg -n "class GatewayRunner" gateway/run.py
rg -n "prompt.submit|message.delta|tool.start" tui_gateway ui-tui apps/desktop
rg -n "COMMAND_REGISTRY|resolve_command" hermes_cli gateway tui_gateway apps/desktop
```

## Exercise: ownership matrix

For a new “show current working directory” feature, describe separately:

- the source of truth for the directory;
- the RPC/event field, if structured clients need it;
- classic CLI rendering;
- TUI rendering;
- desktop rendering;
- gateway command response.

The goal is not to force every surface to implement the feature. It is to avoid
making one surface’s representation the shared source of truth.

## Checkpoint

- Why should the dashboard not rebuild the primary chat in React?
- What is the common boundary between platform adapters and `GatewayRunner`?
- Which file owns slash-command aliases?
- When is a `tui_gateway` change appropriate instead of an `AIAgent` change?
