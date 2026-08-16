# Learning Hermes Agent

This directory is a code-reading course for understanding Hermes Agent as a
system. It is intentionally different from the user documentation: the goal is
to teach where responsibilities live, how information crosses boundaries, and
where a change should be made without coupling unrelated parts of the project.

The central idea is:

> Hermes has one conversation engine, many delivery surfaces, and most optional
> capability lives behind registries, adapters, providers, plugins, or skills.

## The map in one page

```text
                              USER / CALLER
                                   |
          +------------------------+------------------------+
          |                        |                        |
      CLI / TUI              Messaging gateway         ACP / batch / API
          |                        |                        |
          +------------ surface-specific adaptation -------+
                                   |
                            AIAgent orchestration
                    prompt -> model -> tools -> repeat
                      |          |          |
                context/state  provider   capability
                    policy      runtime     registry
                      |                     |
                SQLite/files          tools / MCP / plugins
```

The most important boundaries are:

1. **Surface vs. agent core** — interfaces translate user or protocol events;
   `AIAgent` owns model-driven conversation behavior.
2. **Agent core vs. provider transport** — the loop decides *when* to call a
   model; provider/runtime code decides *how*.
3. **Agent core vs. tools** — the model sees schemas; the registry dispatches
   calls to implementations.
4. **Live conversation vs. persisted state** — in-memory messages drive the
   current turn; session stores make conversations resumable and searchable.
5. **Core vs. extensions** — skills, plugins, MCP servers, provider ABCs, and
   adapters add behavior without widening the permanent core.

## Course order

| Lesson | Question it answers | Main output |
|---|---|---|
| [01 — System model](01-system-model.md) | What kind of system is Hermes? | A stable mental model and vocabulary |
| [02 — Layers and dependency direction](02-layers-and-dependencies.md) | What may depend on what? | Layer map and boundary rules |
| [03 — Agent runtime](03-agent-runtime.md) | What happens during one turn? | End-to-end conversation trace |
| [04 — Tools and capabilities](04-tools-and-capabilities.md) | How does an action become available to a model? | Registration, filtering, dispatch, safety |
| [05 — Surfaces and transports](05-surfaces-and-transports.md) | How do CLI, gateway, TUI, desktop, and ACP differ? | Adapter and ownership map |
| [06 — State, context, and memory](06-state-context-and-memory.md) | What is remembered, where, and for how long? | State taxonomy and persistence boundaries |
| [07 — Extension seams](07-extension-seams.md) | Where should a new capability go? | Decision ladder and extension contracts |
| [08 — Change playbook](08-change-playbook.md) | How do I safely modify the project? | Tracing recipes and test strategy |
| [09 — Code atlas](09-code-atlas.md) | Where is the code for a concept? | Fast lookup reference |

## Hands-on practice

The conceptual lessons above are paired with executable labs in the
[`hands-on/`](hands-on/) directory:

- [Learn the TypeScript TUI first](hands-on/00-ui-tui-first-look.md) — learn
  the React/Ink structure, TypeScript file roles, and UI state before crossing
  into the Python gateway.
- [Trace one TUI message in a debugger](hands-on/01-tui-message-debugging-lab.md)
  — configure TypeScript and Python debuggers, then follow one message through
  JSON-RPC, `AIAgent.run_conversation()`, streaming events, and persistence.

Read lessons 1–3 in order. After that, choose the track closest to the work you
want to do:

- Agent behavior: 04 → 06 → 07
- UI or messaging: 05 → 06 → 08
- Providers and integrations: 04 → 07 → 08
- Persistence and memory: 06 → 03 → 08

## How to use the lessons

For each lesson:

1. Read the model before opening source files.
2. Follow the “code walk” using `rg`; do not read large orchestrator files from
   top to bottom.
3. Answer the checkpoint questions without looking back.
4. Complete at least one exercise in a throwaway branch.
5. Use [09 — Code atlas](09-code-atlas.md) when a name is unfamiliar.

Useful commands:

```bash
# Locate definitions and callers
rg -n "class AIAgent|def run_conversation" run_agent.py agent tests
rg -n "handle_function_call\(" . -g '*.py'

# Find module boundaries through imports
rg -n "^(from|import) (agent|tools|gateway|hermes_cli)" -g '*.py'

# Find behavioral tests for a symbol or RPC method
rg -n "run_conversation|prompt.submit|MessageEvent" tests tests-js apps ui-tui
```

## Authoritative companion references

These lessons provide the learning path; the existing developer guide supplies
deeper subsystem detail:

- [Architecture overview](../../website/docs/developer-guide/architecture.md)
- [Agent loop internals](../../website/docs/developer-guide/agent-loop.md)
- [Prompt assembly](../../website/docs/developer-guide/prompt-assembly.md)
- [Provider runtime](../../website/docs/developer-guide/provider-runtime.md)
- [Tools runtime](../../website/docs/developer-guide/tools-runtime.md)
- [Session storage](../../website/docs/developer-guide/session-storage.md)
- [Gateway internals](../../website/docs/developer-guide/gateway-internals.md)
- [Plugin guide](../../website/docs/developer-guide/plugins/index.md)

## Vocabulary warning

“Model” is overloaded in this project. These lessons use:

- **system model** for the conceptual architecture;
- **domain model** for objects such as a session, message, tool, job, or event;
- **LLM/model** for the inference model selected by the user;
- **provider runtime** for the credentials, URL, API mode, and transport used to
  call that LLM.
