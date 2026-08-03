# Lesson 07 — Extension Seams

## Learning goals

After this lesson you should be able to select an extension mechanism, identify
its contract, and avoid widening the agent core for optional behavior.

## 1. Extension mechanism matrix

| Mechanism | Best for | Model-schema cost | Core coupling |
|---|---|---:|---:|
| Extend existing module/tool | variation of existing behavior | none/new schema not required | low |
| CLI command + skill | procedural workflows using existing capabilities | none | low |
| `check_fn`-gated tool | structured action useful only with configured service | only when available | medium |
| Plugin | niche, third-party, or user-specific integration | selected plugin only | low |
| MCP server | reusable external structured tools | selected server only | low |
| Provider implementation/plugin | alternate model, memory, context, media, or search backend | none or scoped | low |
| Platform adapter/plugin | new messaging channel | none in model core | low |
| Gateway/plugin hook | lifecycle observation or narrowly justified intervention | none | medium |
| New core tool | universal primitive unavailable through existing surfaces | every enabled turn | high |

## 2. Skills

Choose a skill when the agent can already perform the work through terminal,
file, browser, existing tools, or a CLI. A skill teaches procedure without
adding a permanent model tool.

Good examples:

- a project-specific release checklist;
- a workflow around `hermes cron`;
- a research playbook;
- setup instructions for an external CLI.

A skill is not appropriate when reliable execution requires a structured,
typed API unavailable through existing actions.

## 3. Plugins

The plugin manager discovers user, project, bundled, and entry-point plugins.
Plugins can register tools, hooks, middleware, commands, skills, and specialized
providers through a context API.

The contract lives in [`hermes_cli/plugins.py`](../../hermes_cli/plugins.py):

- `PluginManifest` describes identity and requirements;
- `PluginContext` exposes supported registration operations;
- `PluginManager` owns discovery and loading;
- hook/middleware helpers provide runtime invocation.

Third-party products should normally ship as standalone plugin repositories,
not under this repository’s core tree. This keeps maintenance ownership with
the integration author.

Deep reference: [Build a Hermes Plugin](../../website/docs/developer-guide/plugins/index.md).

## 4. MCP

Use MCP when a capability genuinely benefits from structured tool I/O and
should be reusable by other MCP hosts. Hermes discovers configured MCP tools at
surface-appropriate startup points and exposes them through the same effective
tool interface.

MCP avoids hard-wiring each external service into the core. Its boundary is a
protocol, process/connection lifecycle, and dynamic schema catalog.

## 5. Provider abstractions

Several capabilities use a provider ABC plus registry or plugin selection:

- model inference;
- memory;
- context engines;
- browser;
- web search;
- image generation;
- video generation;
- transcription and text-to-speech;
- cron scheduling providers.

When several integrations implement the same category, prefer one shared
contract and orchestrator over unrelated one-off code paths.

Representative contracts:

- [`providers/base.py`](../../providers/base.py)
- [`agent/memory_provider.py`](../../agent/memory_provider.py)
- [`agent/context_engine.py`](../../agent/context_engine.py)
- [`agent/browser_provider.py`](../../agent/browser_provider.py)
- [`agent/web_search_provider.py`](../../agent/web_search_provider.py)
- [`agent/image_gen_provider.py`](../../agent/image_gen_provider.py)

## 6. Platform adapters

A messaging platform adapter implements
`BasePlatformAdapter` and translates platform-specific events and send
semantics. It should not implement a second session model or agent loop.

Use [`gateway/platforms/ADDING_A_PLATFORM.md`](../../gateway/platforms/ADDING_A_PLATFORM.md)
and the [platform adapter guide](../../website/docs/developer-guide/adding-platform-adapters.md).

## 7. Hooks and middleware

Hooks are appropriate for concrete lifecycle consumers. They are dangerous as
speculative infrastructure because once plugins depend on a callback shape,
removing or changing it becomes a compatibility burden.

Before adding a hook:

1. Name the concrete consumer.
2. Show why an existing hook/command/provider/tool contract is insufficient.
3. Define ordering, failure, mutation, and threading semantics.
4. Keep payloads stable and surface-neutral.
5. Add end-to-end proof that the consumer works through discovery and runtime.

## 8. Decision tree

```text
Can existing code/tool express the capability?
  yes -> extend it
  no
Can terminal/file/browser + instructions express it reliably?
  yes -> CLI command if needed + skill
  no
Is it one optional configured service with structured I/O?
  yes -> service-gated tool, plugin, or provider contract
  no
Is it an external reusable tool protocol?
  yes -> MCP server
  no
Is it a new implementation of an existing category?
  yes -> provider/plugin/adapter
  no
Is it fundamental to almost every Hermes user?
  yes -> consider a core tool after design review
  no -> plugin or skill
```

## 9. Separation tests for a design

A healthy extension should pass these questions:

- Can it be disabled without changing unrelated conversations?
- Does its failure degrade only its own capability?
- Is discovery separate from execution?
- Is configuration integrated with `hermes tools`, `hermes setup`, plugins, or
  another existing UX rather than a raw behavioral env var?
- Does it preserve prompt stability and role alternation?
- Is the model schema present only when useful?
- Can its contract be tested without a specific UI?
- Does its real integration path have an E2E test?

## Exercises

Choose an extension seam for each:

1. A new LLM inference company.
2. A custom internal issue tracker used by one organization.
3. A repeatable code-review workflow using existing git and file tools.
4. A new chat network.
5. A second context-compression algorithm.
6. A universal primitive that cannot be performed through terminal, files,
   browser, plugins, or MCP.

Likely answers: model-provider plugin; standalone plugin/MCP; skill; platform
adapter plugin; context-engine provider plugin; only then consider a core tool.

## Checkpoint

- Why is discovery separate from execution?
- When is a provider ABC preferable to several independent plugins?
- What makes a hook non-speculative?
- Can you walk the footprint ladder without looking it up?
