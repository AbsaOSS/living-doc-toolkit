# SPEC — prospective-spec process for the Living Documentation Toolkit

## Status

Process document — no pending specifications (see [§6](#6-pending-specifications)).

---

## 0. Document lifecycle

`SPEC.md` describes behaviour that does **not** exist yet. Every new service, adapter, or
cross-cutting contract change in this monorepo is specced here **before** it is implemented,
the same way `living-doc-collector-gh/SPEC.md` specs a new collector mode before code.

When a section here is implemented, that same PR **moves** the section's content out of
`SPEC.md` and into the live, "what actually exists" docs:

- [`docs/architecture.md`](docs/architecture.md) — system shape, data flow, package structure;
- [`docs/contracts.md`](docs/contracts.md) — CLI arguments, schemas, exit codes, change control;
- `packages/<package>/README.md` / `docs/cookbooks/<service>.md` — service-specific behaviour;
- [`DEVELOPER.md`](DEVELOPER.md) — local-dev workflow;
- [`README.md`](README.md) — user-facing usage and examples.

It is a **move, not a copy**: the section is deleted from `SPEC.md` in the same PR, so the
spec shrinks toward empty instead of drifting out of sync with what shipped. When `SPEC.md`
has no remaining prospective content it stays as this process document only — the
"Pending specifications" list is empty, never stale "✅ implemented" entries.

---

## 1. When a spec is required

Write a spec section here, and land it as its own PR (or as the first commit of the
implementation PR, reviewed before the code), when a change:

- **adds a new service** — a new `packages/services/<name>/` package with a CLI command;
- **adds a new adapter** — a new `packages/adapters/<name>/` package;
- **adds or changes an external contract** — a CLI argument, an input/output schema, an
  exit code, an error-message prefix, the `AdapterResult` signature, or the audit envelope
  (the items under *Stable* and *Requires review* in [`docs/contracts.md`](docs/contracts.md#change-control));
- **adds a new dataset package** — a new `packages/datasets_*/` contract surface.

Internal refactors, new optional fields, new optional CLI arguments, and test/doc/logging
changes do **not** need a spec (they are *Safe to change* in `docs/contracts.md`).

---

## 2. Service spec — required contents

A new-service spec section must cover, in this order:

1. **Overview & scope** — what the service does, what it explicitly does not do, where it
   sits in the pipeline (`collect → normalize → generate`).
2. **CLI interface** — the `living-doc <command>` name, every argument (type, required,
   default, description), and the exit-code table with error-message prefixes. Match the
   shape of the existing entries in [`docs/contracts.md`](docs/contracts.md#cli-interface).
3. **Inputs** — every input file, its producer, its schema/version, and the compatibility
   policy (confirmed range, out-of-range behaviour).
4. **Output contract** — the output file, its `schema_version`, its full structure, and the
   JSON Schema / Pydantic model that is the source of truth.
5. **Algorithm & rules** — the transformation, stated deterministically; every mapping
   table, edge case, and tie-break rule. Call out anything order-dependent.
6. **Audit trail** — the `trace[]` step this service appends (`step`, `tool`,
   `tool_version`) and any warnings it can raise.
7. **Package layout** — `packages/services/<name>/src/living_doc_service_<name>/` module
   map, the pure-vs-I/O split (pure transformation modules take parsed input and return
   structured data — no I/O, no logging setup, no env access), and the
   `apps/cli/commands/<name>.py` command wiring.
8. **Dependencies** — which of `core`, `datasets_*`, `adapters/*` the service package may
   depend on (respect the dependency rules in
   [`docs/architecture.md`](docs/architecture.md#package-dependencies)).
9. **Testing requirements** — the unit tests per module (success + failure paths), the
   fixtures, and the ≥ 80 % per-package coverage gate. Name the golden-fixture directories
   where cross-version compatibility is asserted
   (`tests/fixtures/collector_gh/v<X.Y.Z>/` at the repo root — discovered automatically,
   never a hard-coded version list).
10. **Acceptance criteria** — phase-by-phase, each criterion verifiable against a literal
    code path (a return annotation, a sort call, a guard position, an output string), not
    against "a same-named test is green".

Follow the *Adding a New Service* steps in
[`docs/architecture.md`](docs/architecture.md#adding-a-new-service): create the package,
`service.py`, dependencies, unit tests, the CLI command, register it in `apps/cli/main.py`,
and add a cookbook + recipes under `docs/`.

---

## 3. Adapter spec — required contents

A new-adapter spec section must cover:

1. **Producer identity** — the `metadata.producer.name` value it detects and the semver
   shape of `metadata.producer.version`.
2. **Detection** — the `can_handle(payload) -> bool` rule.
3. **Compatibility policy** — the confirmed version range, and the behaviour for
   within-range (proceed silently), out-of-range (log warning, add
   `VERSION_MISMATCH` to `audit.trace[].warnings[]`, attempt processing), and
   unrecognisable schema (exit with `Adapter error:`).
4. **Parsing** — the mapping from the external payload to `AdapterResult` (metadata →
   audit fields, items → `AdapterItems`), and where the original payload is preserved
   (`audit.extensions["<adapter>"].original_metadata`).
5. **Models** — the adapter-specific types in `models.py`.
6. **Package layout** — `packages/adapters/<name>/src/living_doc_adapter_<name>/`
   (`detector.py`, `parser.py`, `models.py`), depending only on `core`.
7. **Registration** — how the service adapter registry picks it up.
8. **Testing requirements** — fixture files per supported producer version, detection and
   parsing tests, compatibility-warning tests.
9. **Acceptance criteria** — as in [§2](#2-service-spec--required-contents).

Follow the *Adding a New Adapter* steps in
[`docs/architecture.md`](docs/architecture.md#adding-a-new-adapter).

---

## 4. Cross-cutting contract changes

A change to an existing external contract (schema field, CLI argument, exit code, error
prefix, `AdapterResult`, audit envelope) is specced here first with:

- the **before / after** of the contract;
- the **version impact** — additive (no bump), or breaking (major bump of the affected
  schema / package), per [`docs/contracts.md`](docs/contracts.md#change-control);
- the **migration** — how existing callers and fixtures are updated in the same PR;
- the **test-update plan** — every golden fixture and contract test that must change.

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

*None.* All six packages — `core`, `datasets_pdf`, `adapters/collector_gh`,
`services/normalize_issues`, `services/coverage_matrix`, `apps/cli` — are implemented; their
behaviour lives in the live docs listed in [§0](#0-document-lifecycle). Add the next
prospective spec section below this line.
