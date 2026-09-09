# Synthetic coverage-matrix fixtures

The `golden/` fixtures next door are **real** `collector-gh` output (see
`../corpus/` and `../generate_golden_inputs.py`). They exercise the happy path plus
the edge cases the `.feature` corpus can express naturally (a deprecated AC, a stale
`@AC:` ref, an unlinked scenario).

These `synthetic/` fixtures are **hand-authored** and deliberately kept. They cover
shapes the corpus does not produce on its own:

- `empty_doc_source.json` / `empty_ui_tests.json` — empty inputs (no user stories, no
  scenarios).
- `collision_doc_source.json` / `collision_ui_tests.json` — two User Stories that share
  the short id `US-1` across different sources (`absa-group` and `other-org`), an
  `@AC:` reference to an AC that does not exist (`US-1-77`, an unmatched / stale AC),
  and a scenario for an unresolved User Story (`US-5`).

The matcher's remaining edge cases (functionality coverage, multi-test ACs, null
`us_id`) are covered by the unit tests in `tests/test_matcher.py`.
