# SPEC — prospective-spec process for the Living Documentation Toolkit

## Status

Process document — no pending specifications (see [§6](#6-pending-specifications)).

---

## 0. Document lifecycle

`SPEC.md` describes behaviour that does **not** exist yet. Every new command, package, or
cross-cutting contract change in this monorepo is specced here **before** it is implemented,
the same way `living-doc-collector-gh/SPEC.md` specs a new collector mode before code.

When a section here is implemented, that same PR **moves** the section's content out of
`SPEC.md` and into the live, "what actually exists" docs:

- [`README.md`](README.md) — user-facing usage and examples: the action's commands, inputs and output;
- [`DEVELOPER.md`](DEVELOPER.md) — local-dev workflow, the quality gates and CI;
- the package's own `README.md` — package-specific behaviour, e.g.
  [`packages/core/README.md`](packages/core/README.md) for the reader table and the shared input
  validation, [`apps/cli/README.md`](apps/cli/README.md) for the `living-doc` command group.

It is a **move, not a copy**: the section is deleted from `SPEC.md` in the same PR, so the
spec shrinks toward empty instead of drifting out of sync with what shipped. When `SPEC.md`
has no remaining prospective content it stays as this process document only — the
"Pending specifications" list is empty, never stale "✅ implemented" entries.

The contracts themselves — their schemas, models, error codes and pipeline rules — are
[`living-doc-utilities`](https://github.com/AbsaOSS/living-doc-utilities)' and are specced
there, never here.

---

## 1. When a spec is required

Write a spec section here, and land it as its own PR (or as the first commit of the
implementation PR, reviewed before the code), when a change:

- **adds a new command** — a `living-doc <command>` the action runs;
- **adds a new package** — a new `packages/<name>/` or `apps/<name>/` package;
- **reads a new contract** — a new row in the reader table (`living_doc_core.readers.READERS`);
- **adds or changes an external contract of the toolkit** — a CLI argument, an action input or
  output, an exit code, or an error line a caller reads.

Internal refactors, new optional CLI arguments, and test/doc/logging changes do **not** need a
spec.

---

## 2. Command spec — required contents

A new-command spec section must cover, in this order:

1. **Overview & scope** — what the command does, what it explicitly does not do, where it
   sits in the pipeline (`collect → normalize → generate`).
2. **CLI interface** — the `living-doc <command>` name, every argument (type, required,
   default, description), the action inputs it takes, and its exit codes and error lines.
3. **Inputs** — every input file by role (documentation, tests), the contracts each role
   reads through the reader table, and any shared-input-validation step it relies on.
4. **Output contract** — the `living-doc-utilities` contract it writes, through
   `write_artifact`, and what it fills in `metadata.source_inputs[]`.
5. **Algorithm & rules** — the transformation, stated deterministically; every mapping
   table, edge case, and tie-break rule. Call out anything order-dependent.
6. **Lineage** — the command's lineage table (every input path mapped, or dropped with a
   reason) and the field-loss check it runs, per `living-doc-utilities`' component checks.
7. **Package layout** — the package and module map, the pure-vs-I/O split (pure
   transformation modules take parsed input and return structured data — no I/O, no logging
   setup, no env access), and the command's registration in `apps/cli`.
8. **Dependencies** — which packages it depends on, each declared in its own
   `pyproject.toml` (`make deptry` checks it).
9. **Testing requirements** — the unit tests per module (success + failure paths), the
   fixtures (the root `tests/fixtures/` copy, or `living-doc-utilities`' `full_sample`), the
   ≥ 80 % per-package coverage gate, and the `integration.yml` job that runs it through the
   action.
10. **Acceptance criteria** — phase-by-phase, each criterion verifiable against a literal
    code path (a return annotation, a sort call, a guard position, an output string), not
    against "a same-named test is green".

---

## 3. Reader-table spec — required contents

A spec that adds a contract to the reader table must cover:

1. **Contract** — its name and the `living-doc-utilities` version that ships it.
2. **Role** — documentation or tests, and the commands that read it.
3. **Known producers** — every `metadata.producer.name` that writes it.
4. **Shared input validation** — any step the new contract makes reachable (a second
   documentation contract makes `MIXED_DOCUMENTATION_SOURCES` reachable).
5. **Fixtures** — the example file the tests read, and where it comes from.
6. **Acceptance criteria** — as in [§2](#2-command-spec--required-contents).

---

## 4. Cross-cutting contract changes

A change to an existing external contract of the toolkit (CLI argument, action input or
output, exit code, error line) is specced here first with:

- the **before / after** of the contract;
- the **version impact** — additive (no bump), or breaking (major bump of the affected
  package);
- the **migration** — how existing callers and fixtures are updated in the same PR;
- the **test-update plan** — every fixture and contract test that must change.

---

## 5. Review

A spec section is reviewed against:

- **testability** — every acceptance criterion maps to a concrete check on a literal code
  path;
- **determinism** — no nondeterministic behaviour, no hidden side effects, no network
  calls in the transformation path (the pipeline is AI-free and offline — see
  [`README.md`](README.md));
- **contract stability** — existing contracts are unchanged unless the spec explicitly and
  deliberately changes them, with the version impact stated.

The `specification-master` agent (`.github/agents/specification-master.agent.md`) owns the
spec's shape; `sdet` translates acceptance criteria into tests; `reviewer` verifies each
criterion against code at PR time.

---

## 6. Pending specifications

*None.* Both packages — `core` and `apps/cli` — and the action are implemented; their
behaviour lives in the live docs listed in [§0](#0-document-lifecycle). Add the next
prospective spec section below this line.
