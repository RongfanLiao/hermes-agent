# Lesson 06 — State, Context, and Memory

## Learning goals

After this lesson you should be able to classify state by lifetime, distinguish
session history from memory and prompt context, and find the correct persistence
owner for a change.

## 1. State is not one thing

Hermes combines several state scopes:

| Scope | Lifetime | Examples | Typical owner |
|---|---|---|---|
| Call state | one model/tool call | request ID, retry attempt | transport/loop helper |
| Turn state | one user turn | iteration count, active calls, cancellation | `AIAgent` |
| Live session state | process lifetime | active agent, queued prompt, callbacks | surface runner |
| Conversation state | resumable dialogue | messages, title, lineage, usage | session database |
| Profile state | many conversations | config, enabled tools, credentials, logs | profile-aware home |
| Learned state | cross-session knowledge | memory entries, user model | memory provider |
| Project state | working tree lifetime | `AGENTS.md`, project skills, files | filesystem/project |
| Scheduled state | across process restarts | jobs, next run, claims, outputs | cron store |

Before persisting a value, decide its scope. Persisting turn state as profile
state creates stale behavior; keeping conversation identity only in memory
breaks resume.

## 2. Session persistence

[`hermes_state.py`](../../hermes_state.py) provides the SQLite-backed
`SessionDB`. It stores session metadata, role-tagged messages, search indexes,
usage, and lineage across operations such as compression or branching.

The session database answers questions like:

- What messages make up this conversation?
- Which session preceded or followed this one?
- What conversations match a full-text query?
- What title, platform, model metadata, and usage belong to a session?

It does not decide what the agent should remember permanently about the user.

Deep reference:
[Session storage](../../website/docs/developer-guide/session-storage.md).

## 3. Live state vs. database state

Interactive surfaces often maintain a live session object containing an agent,
current history, in-flight text, queued input, callbacks, and locks. The SQLite
record is the durable representation, not necessarily a byte-for-byte snapshot
of every live field.

```text
live surface session                 durable session DB
--------------------                 ------------------
active agent               --->      provider/model metadata
in-flight turn             --->      completed messages
queued correction          --->      persisted after lifecycle transition
callback handles           -X->      not persisted
locks/thread handles       -X->      not persisted
conversation key           <-->      session identity and lineage
```

Resume code reconstructs live state from durable state plus current config. It
should not serialize process objects.

## 4. Prompt context vs. conversation history

These have different roles:

- **System prompt context** defines identity, behavior, available knowledge
  sources, and project instructions for the conversation.
- **Conversation history** records user/assistant/tool interaction.
- **Per-call additions** carry narrowly scoped request information.

Context files such as `AGENTS.md` affect behavior but are not ordinary user
messages. Injecting them as fake conversation turns can violate alternation and
cache stability.

## 5. Memory vs. history

History is an event log for replay. Memory is selected cross-session knowledge.

```text
Conversation A history --+
Conversation B history --+--> memory policy/provider --> selected knowledge
Conversation C history --+                              for future sessions
```

The abstraction is [`agent/memory_provider.py`](../../agent/memory_provider.py),
with orchestration in
[`agent/memory_manager.py`](../../agent/memory_manager.py). Provider plugins can
replace the memory backend without changing the conversation loop’s public
shape.

A useful test:

- If removing the item prevents exact conversation replay, it belongs in
  session history.
- If the item is distilled knowledge useful in unrelated future sessions, it
  belongs in memory.
- If it is a behavioral instruction for work in this directory, it belongs in
  project context.

## 6. Skills

Skills are procedural knowledge loaded on demand. They are not automatically
equivalent to memory and should not all be copied into every system prompt.

- Bundled skills live under [`skills/`](../../skills/).
- Optional skills live under [`optional-skills/`](../../optional-skills/).
- User skills live in the profile’s skills directory.
- Skill slash commands expand into user-requested instructional content while
  preserving prompt-caching rules.

Skills are a low-footprint way to teach the agent how to use existing terminal,
file, browser, or CLI capabilities.

## 7. Configuration, profiles, and secrets

`hermes_constants.get_hermes_home()` is the path boundary for profile-aware
state. A profile isolates configuration, memory, sessions, logs, and gateway
process state.

```text
profile home
  config.yaml       behavioral configuration
  .env / secret     credentials only
  sessions DB       conversation history/search
  memory/           learned state, provider-dependent
  skills/           user-installed procedures
  logs/             runtime diagnostics
  cron/             scheduled state
```

Profiles are independent islands. Clone/copy flows may initialize one profile
from another, but live inheritance would undermine isolation.

## 8. Cron state

[`cron/jobs.py`](../../cron/jobs.py) owns job records, schedules, claims,
heartbeats, next-run calculation, and outputs. [`cron/scheduler.py`](../../cron/scheduler.py)
owns execution and delivery orchestration.

Cron runs should create appropriately isolated agent sessions. They should not
silently borrow the live mutable state of an unrelated interactive session.

Read [Cron internals](../../website/docs/developer-guide/cron-internals.md).

## 9. State-change checklist

For every new field, answer:

1. What is its lifetime and owner?
2. What is its stable identity/key?
3. Must it survive restart, compression, resume, or profile switch?
4. Who writes it, and can writes race?
5. Who reads it, and can the value be stale?
6. Is migration or backward compatibility required?
7. Does it contain credentials or sensitive content?
8. Does it alter the cached prompt prefix?
9. What is the E2E test using a temporary profile home?

## Code walk

```bash
rg -n "^class SessionDB|CREATE TABLE|CREATE VIRTUAL TABLE" hermes_state.py
rg -n "parent_session|lineage|compress" hermes_state.py agent tests
rg -n "^class MemoryProvider|^class MemoryManager" agent plugins/memory
rg -n "get_hermes_home|config.yaml" hermes_constants.py hermes_cli
rg -n "create_job|get_due_jobs|claim_job_for_fire" cron/jobs.py
```

## Exercises

Classify where each item belongs:

1. Tool-call duration for the current spinner.
2. Messages needed to resume yesterday’s session.
3. “The user prefers concise answers” learned across conversations.
4. “Run tests with `scripts/run_tests.sh`” for this repository.
5. A Telegram bot token.
6. A job’s next scheduled execution time.

Answers: live turn/UI state; session DB; memory; project `AGENTS.md`; secret
storage; cron store.

## Checkpoint

- What is lost when live state is reconstructed after restart?
- Why is memory not simply all prior messages?
- Which state must be profile-aware?
- What question should you answer before adding a database column?
