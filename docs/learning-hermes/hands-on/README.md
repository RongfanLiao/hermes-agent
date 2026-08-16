# Hermes Hands-on Practice

This directory contains executable labs for learning Hermes by running,
debugging, and modifying the real system. Conceptual architecture lessons stay
in the [parent learning directory](../README.md).

## Labs

| Lab | What you will practice | Prerequisites |
|---|---|---|
| [00 — Learn the TypeScript TUI first](00-ui-tui-first-look.md) | TUI startup, React/Ink composition, `.ts` versus `.tsx`, state ownership, and one UI-only change | None |
| [01 — Trace one TUI message](01-tui-message-debugging-lab.md) | Environment setup, dual-language debugging, JSON-RPC tracing, agent-loop inspection, streaming, and persistence | Lessons [01](../01-system-model.md), [03](../03-agent-runtime.md), and [05](../05-surfaces-and-transports.md) |

## Practice conventions

Each lab should:

1. state the observable outcome;
2. provide safe environment setup and cleanup;
3. identify exact breakpoint or inspection points by symbol;
4. explain expected values at every boundary;
5. include a completion checklist;
6. distinguish actual production flow from test seams or shortcuts.
