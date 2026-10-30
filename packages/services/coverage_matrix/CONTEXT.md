# living-doc-service-coverage-matrix

Parent: `../CONTEXT.md`

The `coverage-matrix` transform. Its behaviour is [README.md](README.md); this file maps that page to the code.

## Code map

What realises each fact of [README.md](README.md):

- The three files are `living-doc-utilities` contracts; no copy here → utilities
- A run's four steps; nothing written when one fails; no command logs a warning → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/service.py::coverage_matrix`
- An entry per User Story and Functionality, no Feature, in input order → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/builder.py::_matrix_entities`
- An entity's rows → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/builder.py::_entity_coverage`
- A row only for an `active` or `deprecated` criterion → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/builder.py::_is_counted`
- A link matches a criterion by its `id` → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/builder.py::_linked_scenarios`
- A row's aspects, keyword, status and scenarios → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/builder.py::_row`
- An aspect's scenarios and status → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/builder.py::_aspect_coverage`
- A scenario once per aspect or plain row → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/builder.py::_once`
- The summaries and `document.view` → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/builder.py::build_coverage_matrix`
- `planned_summary` → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/builder.py::_planned_summary`
- `metadata.source`, with the tests input's systems → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/builder.py::_source`
- The documentation entry → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/builder.py::_documentation_entry`
- `selected_stats` over the counted records → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/builder.py::_counted_selection`
- The tests entry → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/builder.py::_tests_entry`
- A link warning's code → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/builder.py::_link_warning`
- A link warning's fields → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/builder.py::_warning`
- Link warnings in scenario, then link order → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/builder.py::_link_warnings`
- The lineage table over both inputs → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/lineage.py::LINEAGE_TABLE`
- The table is complete against both inputs → `packages/services/coverage_matrix/tests/test_lineage.py::test_the_lineage_table_accounts_for_every_doc_source_field`, `packages/services/coverage_matrix/tests/test_lineage.py::test_the_lineage_table_accounts_for_every_ui_tests_field`
- Every dropped path says why → `packages/services/coverage_matrix/tests/test_lineage.py::test_every_dropped_path_says_why`
- The run-time field-loss check, against the documentation input → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/service.py::check_no_field_loss`
- Two lists map to one output path: a partial drop goes undetected → `packages/services/coverage_matrix/src/living_doc_service_coverage_matrix/lineage.py::COUNTED_ROOTS`
- The fixture pair against the golden → `packages/services/coverage_matrix/tests/test_service.py::test_the_command_writes_the_committed_fixture_golden`
- The release view differs only in `document.view` → `packages/services/coverage_matrix/tests/test_service.py::test_the_release_view_differs_from_the_golden_only_in_document_view`
- The built inputs → [test_builder.py](tests/test_builder.py)
- The full samples equal `full_sample("coverage-matrix-v1.0.0")` → `packages/services/coverage_matrix/tests/test_service.py::test_over_the_utilities_full_samples_every_entity_and_summary_equals_the_coverage_matrix_samples`
- A builder that drops a mapped field fails with `FIELD_LOSS` → `packages/services/coverage_matrix/tests/test_service.py::test_a_builder_that_drops_a_mapped_field_fails_with_field_loss_and_writes_no_file`
