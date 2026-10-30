# Rule: docs lifecycle — specs shrink as code ships

`SPEC.md` describes what does **not** exist yet — a prospective command, package, or
external-contract change. Once a section is implemented, that section stops being a spec
and becomes a fact about the codebase — so it belongs in the live docs, not in `SPEC.md`.

## The rule

When a PR implements a `SPEC.md` section, that same PR must:

1. **Delete** the implemented content from `SPEC.md` (the whole section, or the specific
   subsections that are now shipped).
2. **Add** the equivalent, "what actually exists" description to the live docs:
   - `docs/action.md` for the action's commands, inputs, output and run-level errors;
     `README.md` only lists them at a glance and links there;
   - the package's own `README.md` (`packages/core/README.md`, `apps/cli/README.md`, a
     command's `packages/services/<command>/README.md`, or a new package's) for
     package-specific behaviour;
   - `DEVELOPER.md` for local-dev workflow, the quality gates and CI.

   Write the new text to the page rules in `DEVELOPER.md`, "Writing documentation", and add each new
   fact's `path::symbol` to the page's code map, the `## Code map` of the `CONTEXT.md` beside its code.

This is a **move**, not a copy. After the PR, the information exists in exactly one place —
the live docs — and `SPEC.md` is smaller. `SPEC.md` trends toward its process-only skeleton
as commands ship.

## What "move" means

- Do not leave the section in `SPEC.md` with a "✅ implemented" marker. Remove it.
- Do not duplicate the schema/flow/table in both `SPEC.md` and a live page. One home.
- If only part of a section shipped, split it: the shipped part moves to live docs, the
  unshipped part stays in `SPEC.md`.
- Cross-references that pointed at the moved `SPEC.md` section must be repointed to its new
  home in the same PR (keep link checks green).

## When SPEC.md has no pending specs

`SPEC.md` in this repo is a **process document** with a "Pending specifications" list. When
that list is empty, leave the process sections in place and the list empty — do not delete
the file. A spec doc that still carries prospective content with nothing tracking it is
drift waiting to happen.
