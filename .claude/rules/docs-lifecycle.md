# Rule: docs lifecycle — specs shrink as code ships

`SPEC.md` describes what does **not** exist yet — a prospective command, package, or
external-contract change. Once a section is implemented, that section stops being a spec
and becomes a fact about the codebase — so it belongs in the live docs, not in `SPEC.md`.

## The rule

When a PR implements a `SPEC.md` section, that same PR must:

1. **Delete** the implemented content from `SPEC.md` (the whole section, or the specific
   subsections that are now shipped).
2. **Add** the equivalent, "what actually exists" description to the live docs:
   - `README.md` for user-facing usage and examples: the action's commands, inputs and output;
   - `DEVELOPER.md` for local-dev workflow, the quality gates and CI;
   - the package's own `README.md` (`packages/core/README.md`, `apps/cli/README.md`, or a new
     package's) for package-specific behaviour.

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
