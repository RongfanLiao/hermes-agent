# Hands-on 01 — Trace One TUI Message in a Debugger

This is a hands-on lab. You will launch the TypeScript TUI from source, attach a
JavaScript debugger to the Ink process, attach a Python debugger to the child
gateway, submit one controlled message, and follow it through the agent loop and
back to the rendered transcript.

## Outcome

By the end, you will have observed this path:

```text
hermes --tui --dev
  -> hermes_cli.main._launch_tui()
  -> ui-tui/src/entry.tsx
  -> GatewayClient.start()
  -> python -m tui_gateway.entry
  -> Ink composer submit
  -> useSubmission.dispatchSubmission()
  -> submitPrompt()
  -> JSON-RPC prompt.submit
  -> tui_gateway.entry.main()
  -> tui_gateway.server.dispatch()
  -> methods_prompt prompt.submit handler
  -> _start_agent_build() -> _make_agent() -> AIAgent(...)
  -> _run_prompt_submit()
  -> AIAgent.run_conversation()
  -> agent.conversation_loop.run_conversation()
  -> model response and optional tool loop
  -> message.delta / message.complete events
  -> createGatewayEventHandler()
  -> turnController
  -> rendered assistant message
```


## Architecture of the debug session

The local TUI contains three relevant process/thread layers:

```text
Python launcher: hermes_cli.main
  |
  +-- Node process: tsx ui-tui/src/entry.tsx
        |
        +-- Python child: python -m tui_gateway.entry
              |
              +-- main stdin JSON-RPC reader thread
              +-- deferred agent-build thread
              +-- per-turn execution thread
```

You need two debuggers because TypeScript and Python run in separate processes.
The gateway also uses worker threads, so enable all-thread Python debugging.

## Part 1 — Prepare the environment

### 1. Open the repository

```bash
cd /home/ubuntu/hermes-agent
```

If your checkout is elsewhere, substitute its absolute path throughout this
guide.

### 2. Create and activate the Python environment

Hermes currently requires Python 3.11 through 3.13. Check that your system
Python is compatible, then create the repository-local environment if it does
not already exist:

```bash
python3 --version
test -d .venv || python3 -m venv .venv
source .venv/bin/activate
python --version
```

On Ubuntu or Debian, if `python3 -m venv .venv` reports that `ensurepip` is
unavailable, install the matching venv package and retry. For example, with
Python 3.12:

```bash
sudo apt update
sudo apt install python3.12-venv
python3 -m venv .venv
source .venv/bin/activate
```

The `python` command may not exist before activation on some Linux
distributions. Once the environment is active, it resolves to
`.venv/bin/python`.

### 3. Install `uv` and the Python development dependencies

Hermes uses `uv` to manage Python packages. If `uv` is not already installed,
install it with the official standalone installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv --version
```

The standalone installer installs `uv` for your user and does not require
`sudo`. The Ubuntu Snap package requires classic confinement, so this guide
does not recommend it.

Then install the development dependencies. The development extra includes
`debugpy`:

```bash
uv pip install -e ".[all,dev]"
python -c "import debugpy; print(debugpy.__version__)"
```

If the standalone installer is unavailable, pip from the active environment is
a supported fallback:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[all,dev]"
python -c "import debugpy; print(debugpy.__version__)"
```

If the environment is already provisioned, the import check is sufficient.

### 4. Install TUI dependencies

From the repository root:

```bash
npm install --workspace ui-tui
npm run build:ink --workspace ui-tui
node --version
```

Node 20 or newer is required. `build:ink` matters because development mode runs
`src/entry.tsx` directly but resolves the local `@hermes/ink` package through
its generated distribution exports.

### 5. Verify the source-mode TUI before debugging

```bash
hermes --tui --dev
```

Confirm that the composer appears, then exit with `/quit`. This separates setup
problems from debugger problems.

#### Optional: isolate the lab in a profile

An isolated profile keeps test sessions out of your normal history:

```bash
hermes profile create tui-debug --clone
hermes -p tui-debug --tui --dev
```

`--clone` copies configuration and credentials into the new profile. Protect
that profile like the default one; it may contain secrets. If you prefer a
fresh profile, omit `--clone` and run setup for it.

The named profile normally lives at:

```text
~/.hermes/profiles/tui-debug/
```

## Part 2 — Create a debugpy launcher

The Node TUI always spawns the gateway as:

```text
<HERMES_PYTHON> -m tui_gateway.entry
```

`HERMES_PYTHON` must be one executable path; it cannot contain arguments. Use a
small temporary executable that inserts `debugpy` before the original `-m`
arguments.

Run this from the repository root:

```bash
export HERMES_DEBUG_REAL_PYTHON="$PWD/.venv/bin/python"
export HERMES_DEBUG_PYTHON=/tmp/hermes-tui-debug-python

printf '%s\n' \
  '#!/usr/bin/env bash' \
  'exec "'"$HERMES_DEBUG_REAL_PYTHON"'" -m debugpy --listen 127.0.0.1:5678 --wait-for-client "$@"' \
  > "$HERMES_DEBUG_PYTHON"
chmod 700 "$HERMES_DEBUG_PYTHON"
```

Inspect it before use:

```bash
sed -n '1,5p' "$HERMES_DEBUG_PYTHON"
```

It should contain an absolute path to this checkout’s Python interpreter.

Why `--wait-for-client`? It pauses before `tui_gateway.entry` is imported, so
you can debug gateway initialization and the first request. Because this delay
would normally trigger the TUI’s 15-second startup warning, the launch commands
below raise the startup timeout.

## Part 3 — Add VS Code debug configurations

Add these entries to `.vscode/launch.json`. If the file already contains
configurations, merge these objects into its `configurations` array.

```jsonc
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Hermes: attach TUI Python gateway",
      "type": "debugpy",
      "request": "attach",
      "connect": {
        "host": "127.0.0.1",
        "port": 5678
      },
      "justMyCode": false
    },
    {
      "name": "Hermes: launch TUI TypeScript directly",
      "type": "node",
      "request": "launch",
      "runtimeExecutable": "${workspaceFolder}/ui-tui/node_modules/.bin/tsx",
      "args": ["src/entry.tsx"],
      "cwd": "${workspaceFolder}/ui-tui",
      "console": "integratedTerminal",
      "sourceMaps": true,
      "skipFiles": ["<node_internals>/**"],
      "env": {
        "NODE_ENV": "development",
        "HERMES_CWD": "${workspaceFolder}",
        "HERMES_PYTHON_SRC_ROOT": "${workspaceFolder}",
        "PYTHONPATH": "${workspaceFolder}",
        "HERMES_PYTHON": "/tmp/hermes-tui-debug-python",
        "HERMES_TUI_STARTUP_TIMEOUT_MS": "300000",
        "HERMES_TUI_RPC_TIMEOUT_MS": "300000"
      }
    }
  ]
}
```

The direct TypeScript launch bypasses `hermes_cli.main`, so the configuration
sets the environment normally prepared by `_launch_tui()`.

If you want the direct launch to use the isolated profile, add this entry to
its `env` object on Linux/macOS:

```jsonc
"HERMES_HOME": "${env:HOME}/.hermes/profiles/tui-debug"
```

### Alternative: debug the real `hermes` launcher path

To include `hermes_cli.main._launch_tui()` in the run:

1. In VS Code, run **Debug: Toggle Auto Attach** and choose `Smart`.
2. Open a VS Code integrated terminal.
3. Launch:

```bash
export HERMES_PYTHON=/tmp/hermes-tui-debug-python
export HERMES_TUI_STARTUP_TIMEOUT_MS=300000
export HERMES_TUI_RPC_TIMEOUT_MS=300000
hermes -p tui-debug --tui --dev
```

VS Code should auto-attach its JavaScript debugger to the `tsx` child. Attach
the Python configuration separately when the child begins listening on port
5678.

Use this alternative when you specifically want to inspect:

- `_resolve_use_tui()`;
- `_make_tui_argv()`;
- `_apply_tui_python_env()`;
- `_launch_tui()` and its constructed child environment.

## Part 4 — Set the breakpoint ladder

Set breakpoints in this order. Line numbers move; set them on the named
statement or function rather than relying on the numbers in this guide.

### Stage A: TUI startup

1. [`ui-tui/src/entry.tsx`](../../../ui-tui/src/entry.tsx)
   - `const gw = new GatewayClient()`
   - `gw.start()`
   - `ink.render(<App gw={gw} /> ... )`

2. [`ui-tui/src/gatewayClient.ts`](../../../ui-tui/src/gatewayClient.ts)
   - `GatewayClient.start()`
   - `startSpawnedGateway()` at the `spawn(...)` call
   - the stdout line handler before `this.dispatch(JSON.parse(raw))`

Inspect:

```text
root
python
cwd
env.HERMES_PYTHON_SRC_ROOT
env.PYTHONPATH
this.proc.pid
```

Expected process arguments:

```text
/tmp/hermes-tui-debug-python -m tui_gateway.entry
```

### Stage B: composer submission

3. [`ui-tui/src/app/useSubmission.ts`](../../../ui-tui/src/app/useSubmission.ts)
   - `submit(value)`
   - `dispatchSubmission(full)`
   - `send(...)`

4. [`ui-tui/src/app/submissionCore.ts`](../../../ui-tui/src/app/submissionCore.ts)
   - `submitPrompt(...)`
   - `startSubmit(...)`
   - the `gw.request('prompt.submit', ...)` call

Inspect the transformation:

| Variable | Meaning |
|---|---|
| `value` | raw composer content |
| `full` | multiline composer content after joining buffered lines |
| `submission.text` | normalized submission text |
| `displayOverride` | transcript text when model-facing content differs |
| `liveSid` | live UI session identifier |
| `submitText` | model-facing RPC text |

You will first see an `input.detect_drop` RPC. That is expected. The client asks
the backend whether the submitted text represents a dropped file before sending
`prompt.submit`.

5. [`ui-tui/src/gatewayClient.ts`](../../../ui-tui/src/gatewayClient.ts)
   - `request<T>(method, params)`
   - the `stdin.write(JSON.stringify(...))` statement

At the second hit, confirm:

```text
method = "prompt.submit"
params = { session_id: <sid>, text: <your message> }
id = "r..."
```

The newline at the end of the JSON string is the stdio frame boundary.

### Stage C: Python JSON-RPC intake

6. Start **Hermes: attach TUI Python gateway**. The child will continue past
   `debugpy.wait_for_client` and import the gateway.

7. [`tui_gateway/entry.py`](../../../tui_gateway/entry.py)
   - `main()`
   - after `req = json.loads(line)`
   - `resp = dispatch(req)`

Inspect:

```text
line
req["id"]
req["method"]
req["params"]
```

8. [`tui_gateway/server.py`](../../../tui_gateway/server.py)
   - `dispatch(req, transport=None)`
   - `handle_request(req)`

`prompt.submit` is normally handled inline long enough to claim the session and
start a deferred turn thread. The RPC response returns quickly with
`{"status": "streaming"}` while model work continues asynchronously.

9. [`tui_gateway/methods_prompt.py`](../../../tui_gateway/methods_prompt.py)
   - the function decorated with `@method("prompt.submit")`
   - `_ensure_session_db_row(session)`
   - `_start_agent_build(sid, session)`
   - `_run_prompt_submit(rid, sid, session, text)` inside
     `run_after_agent_ready()`

The handler is named `_` because its identity is the RPC method string. At
server import time, `HandlerRegistry.install()` rebinds its globals to
`tui_gateway.server`. The debugger still stops in `methods_prompt.py`, but the
call stack and global variables may look unusual.

Inspect:

| Variable | Expected meaning |
|---|---|
| `rid` | request ID generated by `GatewayClient` |
| `sid` | live UI session ID |
| `raw_text` | exact RPC text |
| `text` | sanitized prompt text |
| `session["running"]` | turn ownership/busy guard |
| `session["history"]` | prior model-visible conversation history |
| `session["session_key"]` | durable session identity |

### Stage D: lazy agent construction

The TUI defers construction of the real agent until the first prompt. This
keeps the composer responsive during startup.

10. [`tui_gateway/server.py`](../../../tui_gateway/server.py)
    - `_start_agent_build()`
    - nested `_build()`
    - `_make_agent(...)`
    - `return AIAgent(...)`

Inspect in `_make_agent()`:

```text
model
requested_provider
runtime["provider"]
runtime["api_mode"]
runtime["base_url"]
startup_skills
```

Do not copy credential values from the debugger. Inspect whether a value is
present, not the value itself.

At `return AIAgent(...)`, note these surface-owned inputs:

- `platform` identifies the calling surface;
- `session_id` binds persistence and callbacks;
- `enabled_toolsets` controls eligible capabilities;
- `_agent_cbs(sid)` projects tool and status activity back to the UI;
- the session database belongs to the selected profile.

### Stage E: turn execution

11. [`tui_gateway/server.py`](../../../tui_gateway/server.py)
    - `_run_prompt_submit()`
    - `_emit("message.start", sid)`
    - nested `run()`
    - `result = agent.run_conversation(run_message, **run_kwargs)`

Inspect:

| Variable | Meaning |
|---|---|
| `history` | snapshot taken under `history_lock` |
| `history_version` | detects concurrent history mutation |
| `prompt` | input after context-reference preprocessing |
| `run_message` | final model-facing text or multimodal parts |
| `run_kwargs["conversation_history"]` | prior messages supplied to the agent |
| `run_kwargs["stream_callback"]` | `_stream`, which emits `message.delta` |
| `persist_user_message` | clean transcript form of the prompt |

12. [`run_agent.py`](../../../run_agent.py)
    - `AIAgent.run_conversation()`
    - `AIAgent.chat()`

The first breakpoint fires. The second does not.

`AIAgent.run_conversation()` is now a thin public forwarder that establishes
accounting, relay, and subagent context before calling the extracted loop.

13. [`agent/conversation_loop.py`](../../../agent/conversation_loop.py)
    - module-level `run_conversation(agent, ...)`
    - immediately after `build_turn_context(...)`
    - the main `while` loop
    - `if assistant_message.tool_calls`
    - the `else` branch beginning “No tool calls - this is the final response”
    - `finalize_turn(...)`

After `build_turn_context`, inspect:

```text
user_message
original_user_message
messages
conversation_history
active_system_prompt
effective_task_id
current_turn_user_idx
agent.model
agent.provider
agent.api_mode
agent.valid_tool_names
```

Do not dump `active_system_prompt` or the entire environment into shared logs;
they may contain private context.

At the main loop, watch:

```text
api_call_count
agent.iteration_budget.remaining
agent._budget_grace_call
final_response
```

If the model requests tools, execution returns to the loop after results are
appended. If there are no tool calls, `assistant_message.content` becomes the
candidate final response.

### Stage F: streaming and return path

14. Return to [`tui_gateway/server.py`](../../../tui_gateway/server.py):
    - `_stream(delta)`
    - `_emit("message.delta", sid, payload)`
    - `_emit("message.complete", sid, payload)`
    - the guarded history update comparing `history_version`

The event frame is built by `_event_frame()` and written by `write_json()`.
For stdio mode, it becomes one JSON object per stdout line.

15. Return to [`ui-tui/src/gatewayClient.ts`](../../../ui-tui/src/gatewayClient.ts):
    - stdout line handler
    - `dispatch(msg)`
    - `publish(ev)`

16. [`ui-tui/src/app/createGatewayEventHandler.ts`](../../../ui-tui/src/app/createGatewayEventHandler.ts)
    - `case 'message.start'`
    - `case 'message.delta'`
    - `case 'message.complete'`

Observe:

- `message.start` resets per-turn rendering state;
- `message.delta` feeds streaming text to `turnController`;
- `message.complete` seals the final assistant message, updates usage, and
  returns the composer to ready state.

## Part 5 — Run the trace

### 1. Start TypeScript debugging

Run **Hermes: launch TUI TypeScript directly**.

The terminal will appear paused or waiting because the Python wrapper has
started `debugpy` with `--wait-for-client`.

### 2. Attach Python

Run **Hermes: attach TUI Python gateway**.

Continue through gateway startup until the TUI shows a ready composer.

### 3. Submit a controlled prompt

Use a prompt unlikely to invoke tools:

```text
Reply with exactly TRACE_OK. Do not call any tools.
```

This still makes a real provider request and may incur a small charge. Select a
configured low-cost or local model if desired.

### 4. Walk one breakpoint at a time

Avoid “Step Into” across every library call. Use Continue to move between the
breakpoint stages. The gateway switches from its stdin reader to an agent-build
thread and then to a turn thread; the debugger’s Threads panel will show these
changes.

### 5. Record a trace table

Fill this in while debugging:

| Stage | Thread/process | Input identity | Main value observed | Output identity |
|---|---|---|---|---|
| Composer | Node | — | `value` | `submission.text` |
| RPC send | Node | `sid` | `params.text` | request `id` |
| RPC intake | Python main | request `id` | `req.method` | handler result |
| Prompt handler | Python main/deferred | `sid` | sanitized `text` | running session |
| Agent build | Python build thread | session key | provider/runtime | `AIAgent` |
| Turn bridge | Python turn thread | history version | `run_message` | `run_kwargs` |
| Agent loop | Python turn thread | task/turn ID | `messages` | result dictionary |
| Event emit | Python turn thread | `sid` | delta/final payload | JSON event frame |
| Event consume | Node | `sid` | event type | transcript update |

The same `sid` routes live UI events. The durable `session_key` identifies the
persisted conversation. They are related but not interchangeable.

## Part 6 — Inspect persistence after the turn

Exit the TUI cleanly, then list sessions in the debug profile:

```bash
hermes -p tui-debug sessions list --limit 5
```

The profile database is normally:

```text
~/.hermes/profiles/tui-debug/state.db
```

If `sqlite3` is installed, inspect its shape without assuming a schema version:

```bash
sqlite3 ~/.hermes/profiles/tui-debug/state.db '.tables'
sqlite3 ~/.hermes/profiles/tui-debug/state.db 'PRAGMA table_info(sessions);'
sqlite3 ~/.hermes/profiles/tui-debug/state.db 'PRAGMA table_info(messages);'
```

Use `hermes sessions export` rather than hand-writing SQL when you need a stable
user-facing export. The direct SQLite inspection is only for learning the
storage boundary.

## Part 7 — Debugging without pausing

Breakpoints change thread timing. For race-sensitive behavior, replace them
with debugger logpoints.

Suggested TypeScript logpoints:

```text
submissionCore: submit sid={liveSid} text={submitText}
gatewayClient: rpc id={id} method={method}
gatewayClient: event type={ev.type} sid={ev.session_id}
```

Suggested Python logpoints:

```text
prompt handler rid={rid} sid={sid} text_type={type(text).__name__}
agent build sid={sid} key={key}
turn start sid={sid} history_version={history_version}
agent call session={agent.session_id} model={agent.model} provider={agent.provider}
turn complete sid={sid} status={status} chars={len(raw or '')}
```

Never print arbitrary diagnostics to the gateway’s protocol stdout. Stdio mode
uses newline-delimited JSON there. Use debugger logpoints, Python logging,
`print(..., file=sys.stderr)`, or the profile log directory.

Relevant logs:

```text
~/.hermes/logs/agent.log
~/.hermes/logs/errors.log
~/.hermes/logs/tui_gateway_crash.log
```

For a named profile, replace `~/.hermes` with its profile directory.

## Part 8 — Common problems

### The TUI says the gateway timed out

The Python child is probably waiting for the debugger. Attach to port 5678 or
confirm `HERMES_TUI_STARTUP_TIMEOUT_MS=300000` reached the Node process.

### Port 5678 is already in use

```bash
ss -ltnp | rg ':5678'
```

Stop the stale debug process or choose another port in both the wrapper and
`launch.json`.

### TypeScript breakpoints are hollow or never bind

- Confirm the launch uses `tsx src/entry.tsx`, not `dist/entry.js`.
- Confirm `sourceMaps` is enabled.
- Run `npm run build:ink --workspace ui-tui` again.
- Use the direct Node launch configuration instead of relying on Auto Attach.

### Python breakpoints do not fire

- Confirm the gateway process command contains `debugpy`.
- Confirm VS Code attached before continuing.
- Set `justMyCode: false`.
- Remember that agent build and turn execution occur on background threads.
- Break in `agent/conversation_loop.py`, not only the forwarding method in
  `run_agent.py`.

### `AIAgent.chat()` does not fire

That is expected for the TUI. It is the core lesson of this trace:

```text
TUI -> AIAgent.run_conversation()
chat() -> run_conversation() only for simple programmatic callers
```

### The TUI has no configured model

Run setup for the selected profile or launch with your configured default
profile. Inspect credential presence, but never paste keys into logs or debugger
notes.

### The debugger makes a race disappear

Use logpoints and event IDs instead of pausing. Track `sid`, request `id`,
`session_key`, `history_version`, task ID, and turn ID across the flow.

### Synthetic mode unexpectedly bypasses `AIAgent`

Do not set `HERMES_ISO_CERTIFY_SYNTH_TURN=1` for this lab. That test seam causes
`_make_agent()` to return `SyntheticHeavyAgent`, deliberately bypassing the real
`AIAgent` path.

## Part 9 — Cleanup

Remove the temporary debug launcher:

```bash
rm -f /tmp/hermes-tui-debug-python
unset HERMES_PYTHON HERMES_TUI_STARTUP_TIMEOUT_MS HERMES_TUI_RPC_TIMEOUT_MS
unset HERMES_DEBUG_REAL_PYTHON HERMES_DEBUG_PYTHON
```

Keep or remove the VS Code configurations according to your workflow. A named
debug profile can also be retained for future tracing.

## Completion checklist

You have completed the lab when you can demonstrate all of these:

- [ ] The source-mode Ink TUI launched successfully.
- [ ] JavaScript and Python debuggers were attached simultaneously.
- [ ] You observed `input.detect_drop` before `prompt.submit`.
- [ ] You matched the Node request ID to the Python `rid`.
- [ ] You distinguished live `sid` from durable `session_key`.
- [ ] You observed lazy construction of `AIAgent` on the first prompt.
- [ ] `AIAgent.run_conversation()` fired and `AIAgent.chat()` did not.
- [ ] You entered `agent.conversation_loop.run_conversation()`.
- [ ] You observed the message list after `build_turn_context()`.
- [ ] You followed at least one `message.delta` or `message.complete` event back
  to the TypeScript event handler.
- [ ] You found the persisted session in the selected profile.

## Next experiments

Repeat the lab with one controlled variation at a time:

1. Ask for `read_file` and follow the tool-call branch.
2. Submit a second prompt while the first is running and trace queue/interrupt
   behavior.
3. Resume the session and inspect how history is reconstructed.
4. Add an image and compare `prompt`, `run_message`, and
   `persist_user_message`.
5. Use a slash command and observe where it leaves the normal prompt path.
