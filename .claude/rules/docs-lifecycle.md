# Rule: docs lifecycle — specs shrink as code ships

`SPEC.md` describes what does **not** exist yet — a prospective service, adapter, or
external-contract change. Once a section is implemented, that section stops being a spec
and becomes a fact about the codebase — so it belongs in the live docs, not in `SPEC.md`.

## The rule

When a PR implements a `SPEC.md` section, that same PR must:

1. **Delete** the implemented content from `SPEC.md` (the whole section, or the specific
   subsections that are now shipped).
2. **Add** the equivalent, "what actually exists" description to the live docs:
   - `docs/architecture.md` for system shape, data flow, and package structure;
   - `docs/contracts.md` for CLI arguments, schemas, exit codes, and change control;
   - the package `README.md` or `docs/cookbooks/<service>.md` for service-specific
     behaviour;
   - `docs/recipes/<name>.md` for run-it-in-an-environment guides;
   - `DEVELOPER.md` for local-dev workflow;
   - `README.md` for user-facing usage and examples.

This is a **move**, not a copy. After the PR, the information exists in exactly one place —
the live docs — and `SPEC.md` is smaller. `SPEC.md` trends toward its process-only skeleton
as services ship.

## What "move" means

- Do not leave the section in `SPEC.md` with a "✅ implemented" marker. Remove it.
- Do not duplicate the schema/flow/table in both `SPEC.md` and `docs/contracts.md`. One
  home.
- If only part of a section shipped, split it: the shipped part moves to live docs, the
  unshipped part stays in `SPEC.md`.
- Cross-references that pointed at the moved `SPEC.md` section must be repointed to its new
  home in the same PR (keep link checks green).

## When SPEC.md has no pending specs

`SPEC.md` in this repo is a **process document** with a "Pending specifications" list. When
that list is empty, leave the process sections in place and the list empty — do not delete
the file. A spec doc that still carries prospective content with nothing tracking it is
drift waiting to happen.
