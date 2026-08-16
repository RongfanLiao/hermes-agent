# Hands-on 00 — Learn the TypeScript TUI First

This tutorial introduces only the `ui-tui` module. You will learn how the TUI
starts, how its React/Ink tree is organized, where state lives, and how `.ts`
and `.tsx` files differ. The Python agent and gateway are treated as a black
box for now.

After this tutorial, use
[Hands-on 01](01-tui-message-debugging-lab.md) to trace a message across the
TypeScript/Python boundary.

## Outcome

By the end, you will be able to answer:

1. Which file starts the TUI?
2. Which code owns state and which code draws the screen?
3. When should a file use `.ts` or `.tsx`?
4. Where should you begin when changing one visible TUI element?

You will also make and verify one small UI-only change.

## 1. The smallest useful mental model

The TUI is a Node.js application built with TypeScript, React, and Ink. Ink is
similar to React DOM, but its components draw terminal cells instead of HTML.

```text
terminal keyboard
       |
       v
ui-tui/src/entry.tsx       starts the Node application
       |
       v
ui-tui/src/app.tsx         connects state to the root component
       |
       +--> app/useMainApp.ts       owns and coordinates UI behavior
       |
       +--> components/appLayout.tsx draws the visible screen
       |
       v
ui-tui/src/gatewayClient.ts sends requests to and receives events from Python
```

For now, stop at `gatewayClient.ts`. It is enough to know that the gateway
provides sessions, assistant messages, tool activity, and configuration. You
do not need to understand its Python implementation to learn the TUI.

## 2. Run the TUI from source

From the repository root:

```bash
source .venv/bin/activate
npm install --workspace ui-tui
npm run build:ink --workspace ui-tui
hermes -p tui-debug --tui --dev
```

If the `tui-debug` profile does not exist, create it first:

```bash
hermes profile create tui-debug --clone
```

Development mode runs `src/entry.tsx` through `tsx`, so it reads the TypeScript
source instead of the compiled `dist/entry.js` bundle. It does **not** watch
files or hot-reload. After each source edit, exit with `/quit` and run the
command again to see the change.

## 3. Read only five places

Do not read the entire directory in filename order. Start with these files.

### A. `src/entry.tsx` — boot

[`entry.tsx`](../../../ui-tui/src/entry.tsx) performs process-level work:

- verifies that stdin is a terminal;
- restores safe terminal modes;
- creates and starts `GatewayClient`;
- installs shutdown and memory handling;
- dynamically imports Ink and `App`;
- renders `<App gw={gw} />`.

The most important line is the final render call. It changes the question from
“How does the process start?” to “What does `App` render?”

### B. `src/app.tsx` — root composition

[`app.tsx`](../../../ui-tui/src/app.tsx) is intentionally small:

```tsx
export function App({ gw }: { gw: GatewayClient }) {
  const model = useMainApp(gw)

  return <AppLayout /* grouped values from model */ />
}
```

The real code also provides the gateway through React context and reads shared
UI state from a nanostore. Its architectural job is still simple: obtain the
application model and pass it to the layout.

### C. `src/app/useMainApp.ts` — behavior and state

[`useMainApp.ts`](../../../ui-tui/src/app/useMainApp.ts) is the top-level
composition hook. It connects narrower hooks for:

- composer input;
- session lifecycle;
- prompt submission;
- gateway events;
- configuration synchronization;
- transcript virtualization.

At the end it returns six grouped values:

```text
appActions      callbacks initiated by the UI
appComposer     draft, dimensions, completion and queue data
appProgress     whether progress UI should be visible
appStatus       status-line and timing data
appTranscript   rendered conversation history
gateway         the client and typed RPC helper
```

You do not need to understand every hook. When investigating behavior, find
the relevant returned group and trace backward from there.

### D. `src/components/appLayout.tsx` — screen structure

[`appLayout.tsx`](../../../ui-tui/src/components/appLayout.tsx) composes the
visible regions:

```text
AppLayout
  +-- TranscriptPane     previous and streaming messages
  +-- PromptZone         approval, clarification and secret prompts
  +-- ComposerPane       text input, completions and status
  +-- FloatingOverlays   pickers and dialogs
  +-- optional widgets   pets, rails and performance display
```

The components use Ink primitives such as `<Box>` and `<Text>`. Think of
`Box` as terminal flexbox and `Text` as styled terminal text.

### E. `src/gatewayClient.ts` — the boundary

[`gatewayClient.ts`](../../../ui-tui/src/gatewayClient.ts) is TypeScript, but
it does not draw anything. It starts the Python gateway and exchanges
newline-delimited JSON-RPC messages through stdin/stdout.

The TUI sends requests such as `prompt.submit`. The client publishes incoming
events, and `useMainApp` arranges for those events to update UI state.

That is enough gateway knowledge for this tutorial.

## 4. Understand `.ts` and `.tsx`

Both extensions contain TypeScript.

Use `.ts` when a file contains logic, types, state, or transport code without
JSX:

```ts
export function statusLabel(ready: boolean): string {
  return ready ? 'ready' : 'starting'
}
```

Use `.tsx` when a file contains JSX elements:

```tsx
export function Status({ ready }: { ready: boolean }) {
  return <Text>{ready ? 'ready' : 'starting'}</Text>
}
```

Examples in this module:

| File | Why |
|---|---|
| `gatewayClient.ts` | Process and JSON-RPC logic; no JSX |
| `app/turnStore.ts` | Shared state; no JSX |
| `app.tsx` | Renders `GatewayProvider` and `AppLayout` |
| `components/messageLine.tsx` | Renders message components |

Imports use `.js` even when the source file is `.ts` or `.tsx`, for example:

```ts
import { GatewayClient } from './gatewayClient.js'
```

This is intentional. The module uses Node's `nodenext` resolution, and the
compiled runtime file is JavaScript. Do not rewrite these imports to `.ts`.

## 5. Know the two kinds of UI state

The module primarily uses two state styles:

- React hooks such as `useState` for state owned by one composition path;
- nanostores for shared state read by distant components.

For example, `useMainApp.ts` owns transcript history with React state, while
`app/uiStore.ts`, `app/turnStore.ts`, and `app/overlayStore.ts` expose shared
atoms. Components that render an atom use `useStore(atom)`.

A practical rule:

- keep local behavior local;
- use an existing feature atom when distant components need the same state;
- do not pass the same state through several components merely to reach a leaf.

## 6. Make one visible TUI-only change

In this exercise you will edit TypeScript rendering source, not a configuration
value. The change stays entirely inside `ui-tui`: no Python, gateway, or
`config.yaml` changes are involved.

### 6.1 See the title before changing it

Start the development TUI as described in section 2. A normal-width terminal
shows a large `HERMES-AGENT` title immediately. You do not need to type anything
to reveal it, so the startup screen provides a clear before state.

### 6.2 Find the code that draws the title

Open [`ui-tui/src/banner.ts`](../../../ui-tui/src/banner.ts) in a second
terminal. `LOGO_ART` is an array containing one string for each visible row of
the title:

```ts
const LOGO_ART = [
  '██╗  ██╗███████╗ ...',
  // five more rows
]
```

This is TypeScript data used directly by the TUI—not a skin or configuration
value. The `logo()` function colors these rows, and `Banner` in
`components/branding.tsx` renders them through the Ink `ArtLines` component.
`LOGO_WIDTH` is calculated from the longest row, so responsive layout continues
to work when the artwork changes width.

### 6.3 Replace the title artwork

Replace only the `LOGO_ART` array with this six-row wordmark:

```ts
const LOGO_ART = [
  '██████╗ ██████╗ ██╗███████╗███████╗██╗███╗   ██╗ ██████╗ ',
  '██╔══██╗██╔══██╗██║██╔════╝██╔════╝██║████╗  ██║██╔════╝ ',
  '██████╔╝██████╔╝██║█████╗  █████╗  ██║██╔██╗ ██║██║  ███╗',
  '██╔══██╗██╔══██╗██║██╔══╝  ██╔══╝  ██║██║╚██╗██║██║   ██║',
  '██████╔╝██║  ██║██║███████╗██║     ██║██║ ╚████║╚██████╔╝',
  '╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝ '
]
```

Read the rows vertically: together they spell `BRIEFING`. Both banners have
six rows, so `LOGO_GRADIENT` already has the correct length and must not be
changed. Leave the tagline, colors, and every other component untouched.

Save the file, then confirm that you changed implementation code:

```bash
git diff -- ui-tui/src/banner.ts
```

### 6.4 Restart and observe the changed title

Saving does not update a TUI process that is already running. Return to that
process, enter `/quit`, and launch a fresh development TUI:

```bash
hermes -p tui-debug --tui --dev
```

The large startup title should now read `BRIEFING`.

If `HERMES-AGENT` remains, check all three of these conditions:

1. You saved `ui-tui/src/banner.ts`.
2. You completely exited the old TUI before relaunching it with `--dev`.
3. Your active skin does not provide its own `banner_logo`, which overrides the
   built-in `LOGO_ART`. Use the default skin for this exercise if necessary.

The full artwork is intentionally replaced by a compact banner on narrow
terminals. Use a terminal at least 70 columns wide to see this wordmark.

### 6.5 Understand the render path

Your edit followed this UI-only path:

```text
banner.ts LOGO_ART
  -> logo()
  -> Branding Banner
  -> ArtLines
  -> Ink Text
  -> terminal cells
```

No state or gateway event is required: `AppLayout` renders the banner at
startup. Keep the change while you run the checks in section 7. Afterward, you
may restore the original artwork if you want a clean working tree.

## 7. Verify TUI work

Run focused checks from the repository root:

```bash
npm run typecheck --workspace ui-tui
npm run lint --workspace ui-tui
npm test --workspace ui-tui
```

During development, prefer a focused test when one exists:

```bash
cd ui-tui
npx vitest run src/__tests__/messageLine.test.ts
```

## Completion checklist

- [ ] I can identify `entry.tsx`, `app.tsx`, `useMainApp.ts`, and `appLayout.tsx`.
- [ ] I understand that Ink renders terminal components, not browser HTML.
- [ ] I know why `gatewayClient.ts` is `.ts` and UI components are `.tsx`.
- [ ] I can distinguish local React state from shared nanostores.
- [ ] I changed only `LOGO_ART` in `banner.ts` and observed the new `BRIEFING` title.
- [ ] I used `git diff` to confirm that I changed source code, not configuration.
- [ ] I ran the TUI checks, then kept or restored the practice change intentionally.

## Next step

Continue with
[Hands-on 01 — Trace One TUI Message in a Debugger](01-tui-message-debugging-lab.md).
That lab adds the TypeScript debugger, the Python gateway debugger, JSON-RPC,
and the agent loop after the TUI structure is familiar.
