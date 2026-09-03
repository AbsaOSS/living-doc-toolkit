# `.claude/` helper set

Productivity helpers for roadmap/spec-driven work in `living-doc-toolkit`. Copied and
adapted from the ecosystem reference copy in `living-doc-collector-gh/.claude/` (the
repo-specific parts here are the monorepo `make` vocabulary, the mock/fixture table, and
the doc paths).

These helpers are **acceleration, not dependency**. Every task they describe can be done by
hand, just slower. Nothing in CI or the release path requires them.

## What's here

| File | Kind | Purpose |
|---|---|---|
| `commands/implement-task.md` | slash command | Drive one roadmap task from its spec to a PR-ready description. |
| `commands/verify-pr-ready.md` | slash command | Verify-only gate: is this branch PR-ready? one yes/no. |
| `agents/test-author.md` | subagent | Write deterministic pytest tests using this repo's real mock/fixture surface. |
| `rules/docs-lifecycle.md` | rule | Implemented `SPEC.md` sections **move** into the live docs. |

## How the two commands relate

Both check **acceptance criteria against the actual code** — reading the return annotation,
the sort call, the guard position, the literal `pyproject.toml` value — never "a test with
that name is green".

- **`/implement-task <id>`** is the full lifecycle: read the task → read every referenced
  file → implement → `make qa` (or `make qa-<alias>`) until green → verify each acceptance
  criterion against code → write the `## Overview` / `## Release Notes` / `## Related` PR
  description → stop. It collapses the `specification-master` → `senior-developer` →
  `sdet` → `reviewer` agent sequence into one driven command.

- **`/verify-pr-ready <id>`** is the lighter companion for right before opening a PR —
  useful when a human did most of the implementation. It re-checks every acceptance
  criterion against code, runs `make qa`, runs the `reviewer` agent, and outputs a single
  `PR-READY: yes/no` with a specific fix list when the answer is no. It does not implement
  anything.

Typical flow: `/implement-task` to build it, then `/verify-pr-ready` as the final gate
before opening the PR.

## Relationship to `.github/agents/`

The `.github/agents/` board (`specification-master`, `senior-developer`, `sdet`,
`reviewer`, `devops-engineer`) stays the source of truth for role behavior. `test-author`
here is `sdet` plus the concrete repo mock table; `/verify-pr-ready` invokes `reviewer`.
