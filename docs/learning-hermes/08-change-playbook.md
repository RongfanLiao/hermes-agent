# Lesson 08 — Change and Debugging Playbook

## Learning goals

After this lesson you should be able to verify a reported premise, trace all
sibling call paths, make a narrowly placed change, and select tests that prove
the real integration.

## 1. Start from behavior, not a guessed file

Write the symptom as an observable contract:

```text
Given <initial state and surface>
When <event or user action>
Then <expected behavior>
But currently <observed behavior>
```

Then identify:

- the input boundary;
- the canonical domain object;
- the decision point;
- the side-effect boundary;
- the persisted outcome;
- sibling surfaces that reuse the same contract.

## 2. Verify the premise

Before changing code:

1. Reproduce on the current branch.
2. Point to the exact decision or state transition producing the symptom.
3. Use `git log -p -S '<symbol>' -- <file>` when an omission or restriction may
   be intentional.
4. Check whether an earlier guard makes the proposed branch unreachable.
5. Identify tests that encode the current behavior and whether they represent
   intent or accident.

A plausible story is not a reproduction.

## 3. Trace by contract

### Missing tool

```text
module -> register -> discovery -> toolset filter -> check_fn -> schema refresh
```

### Wrong gateway response

```text
platform event -> MessageEvent -> auth/session guard -> command or agent turn
-> callbacks/final text -> delivery -> platform send
```

### Wrong model/provider

```text
surface request -> config/profile -> runtime resolution precedence
-> transport selection -> persisted session runtime
```

### Broken resume

```text
session key -> DB record/lineage -> stored messages -> normalization
-> live session reconstruction -> agent history
```

### UI drift

```text
source of truth -> RPC/event/catalog -> client store -> component projection
```

Stop tracing when you find the earliest point where actual data diverges from
the contract. Fixing later presentation often hides the real bug.

## 4. Search recipes

```bash
# Definition, callers, and tests
rg -n "def target_name|class TargetName" . -g '*.py'
rg -n "target_name\(" . -g '*.py'
rg -n "target_name|expected visible phrase" tests tests-js apps ui-tui

# Import direction
rg -n "^(from|import) .*target_module" . -g '*.py'

# Historical intent
git log --oneline --all -- path/to/file.py
git log -p -S 'target_name' -- path/to/file.py

# Relevant recent changes
git log -n 10 --stat -- path/to/file.py tests/relevant_area
```

## 5. Choose the fix location

Use the earliest shared owner of the violated invariant:

| Symptom across… | Likely fix boundary |
|---|---|
| every surface | agent/state/provider/tool shared layer |
| every messaging platform | gateway common layer |
| one messaging platform | its adapter |
| TUI and dashboard | `ui-tui` |
| TUI and desktop structured state | `tui_gateway` contract plus clients |
| one tool backend | backend adapter |
| every implementation of a provider category | provider contract/orchestrator |

Do not centralize merely because code looks similar. Centralize shared policy
or invariant; leave representation-specific behavior at the edge.

## 6. Test pyramid for Hermes changes

### Pure/unit tests

Use for parsers, normalization, scheduling calculations, schema filtering,
error classification, and state transitions.

### Contract tests

Use for provider transports, platform adapters, plugin manifests, RPC payloads,
tool schemas, and message-role invariants.

### Integration tests

Use real imports and a temporary `HERMES_HOME` for configuration propagation,
plugin discovery, session persistence, provider resolution, tool availability,
and migrations.

### End-to-end tests

Use for resume, real file/network boundaries, security/approval flows, gateway
delivery, TUI/desktop event sequences, and cross-module lifecycle behavior.

Mocks are useful at external service boundaries. They should not replace the
internal path the change claims to fix.

## 7. Test invariants, not snapshots

Prefer:

- “the resumed session contains the same completed user/assistant turns”;
- “every advertised tool name resolves to a handler”;
- “a tool result references the corresponding call ID”;
- “a disabled plugin contributes no runtime registrations”;
- “next run is later than the successful execution under this schedule.”

Avoid freezing:

- the exact number of tools, providers, or commands;
- a current model list;
- schema version literals without migration behavior;
- an entire prompt when only one relationship matters.

## 8. Minimum completion checklist

- The bug or requested behavior is reproduced or explicitly demonstrated.
- The exact causal line/state transition is identified.
- Historical intent was checked where design ambiguity exists.
- The fix is at the correct separation point.
- Sibling call paths were searched.
- Prompt caching and message alternation remain valid.
- Configuration uses established profile/config UX.
- Optional capability remains optional and gated.
- Unit/contract tests cover the invariant.
- A real integration path is exercised when state, discovery, security, or I/O
  is involved.
- Existing user changes in the worktree are preserved.

## Exercises

1. Pick a recent bug-fix commit. Reconstruct its behavior statement, causal
   line, separation point, and proving test.
2. Pick a gateway feature and list its sibling platform paths.
3. Find a test that freezes a value and rewrite it on paper as an invariant.
4. Trace how a temporary profile home is established in an integration test.

## Checkpoint

- What evidence establishes that a proposed fix changes runtime behavior?
- When should you inspect git history with `-S`?
- Why can a green mocked unit test be insufficient?
- What is the earliest-shared-owner rule?
