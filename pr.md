## Overview

`normalize-issues` now renders one of two **content views**, selected with a new
`--view inner|release` option (default `inner`):

- **`inner`** — comprehensive internal documentation; nothing is filtered.
- **`release`** — public-facing documentation. Entities whose `state` is `planned` or
  `in_review` are dropped entirely; acceptance criteria whose `state` is `planned` or
  `in_review` are dropped from the entities that remain. `deprecated` ACs (and `deprecated`
  entities) are **kept** — they describe behaviour that shipped and is still part of the
  solution. Only not-yet-real content (`planned` / `in_review`) is release-hidden.

The view is a toolkit-level decision, not a per-generator input: the same
`generator-ready.json` contract is produced either way. Every output records the applied
view and how much it filtered at `meta.view`
(`{ view, filtered_user_stories, filtered_acceptance_criteria }`), and
`meta.selection_summary.excluded_items` now reflects view-filtered entities.

State comparison is case-insensitive and folds spaces/`-` to `_`, so `In Review`,
`in-review`, and `in_review` are equivalent.

Docs: `docs/contracts.md` gains a **Content Views** section and a `--view` CLI row.
`SPEC.md` has no pending spec for this (new optional CLI arg + new optional schema field —
*Safe to change* per `docs/contracts.md`), so nothing is moved out of it.

## Release Notes

- `living-doc normalize-issues` accepts `--view inner|release` (default `inner`). The
  `release` view produces public-facing documentation by omitting `planned`/`in_review`
  entities and `planned`/`in_review` acceptance criteria (`deprecated` content is kept);
  `meta.view` in the output records the applied view and the number of entities and
  acceptance criteria that were filtered out.

## Related

Closes #77

## Acceptance criteria

| # | Criterion | Proof |
|---|-----------|-------|
| 1 | `--view inner\|release`, default `inner` | `apps/cli/src/living_doc_cli/commands/normalize_issues.py:89-93,111,137` (`click.Choice([...])`, `default="inner"`) |
| 2 | Release drops `planned` / `in_review` entities | `packages/services/normalize_issues/src/living_doc_service_normalize_issues/builder.py:35,67-69` |
| 3 | Release drops `planned` / `in_review` ACs; keeps `deprecated` | `builder.py:36-38,74-76`; `test_builder.py::test_release_view_drops_planned_and_in_review_acs_but_keeps_deprecated` |
| 4 | Inner view filters nothing | `builder.py:60` (`release_view = view == "release"`) guards every filter branch; `test_builder.py::test_inner_view_keeps_everything` |
| 5 | Output metadata records view + filtered counts | `builder.py:126-132,181`; model `generator_ready/v1/models.py:119-136,145`; `excluded_items` at `builder.py:123-125` |
| 6 | Filter spec in `docs/contracts.md` | `docs/contracts.md:28,198,231-263` (Content Views section) |
| 7 | One input → both views as goldens; `planned` entity & `deprecated` AC in inner not release | `tests/fixtures/views/{input,expected_inner,expected_release}.json`; `packages/services/normalize_issues/tests/integration/test_view_golden_files.py` |
| 8 | All tests / QA green | `make qa-datasets-generator-ready`, `make qa-normalize`, `make qa-cli`, `make integration` all pass |

🤖 Generated with [Claude Code](https://claude.com/claude-code)
