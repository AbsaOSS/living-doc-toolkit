# living-doc-service-normalize-tests

Parent: `../CONTEXT.md`

The `normalize-tests` transform. Its behaviour is [README.md](README.md); this file maps that page to the code.

## Code map

What realises each fact of [README.md](README.md):

- The three files are `living-doc-utilities` contracts; no copy here → utilities
- A run's four steps; nothing written when one fails; one documentation input → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/service.py::normalize_tests`
- Grouping by feature file and linked entity, the order, unlinked scenarios, the envelope, forwarded warnings → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/builder.py::build_ui_test_catalog`
- A feature file's key and name → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/builder.py::_feature_file`
- The repository-qualified name relies on the collector's `scenario_id` shape → collector-gh
- A feature file's background, its first scenario's → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/builder.py::build_ui_test_catalog`
- A link's entity id, once per entity → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/builder.py::_entity_ids`
- A `CatalogScenario` without its background, each link with its state → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/builder.py::_catalog_scenario`
- The criteria whose states a link reads, a User Story's or a Functionality's → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/builder.py::_criteria_states`
- The release view drops `planned` and `in_review` links → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/builder.py::_kept_links`
- The states the release view drops → `packages/core/src/living_doc_core/views.py::RELEASE_DROPS`
- The documentation entry's `selected_stats` over every record → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/builder.py::build_ui_test_catalog`
- The tests entry's `selected_stats` over the links the view keeps → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/builder.py::_tests_selection`
- A group per entity, opened on its first link → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/builder.py::_place`
- The lineage table → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/lineage.py::LINEAGE_TABLE`
- The table is complete against both inputs → `packages/services/normalize_tests/tests/test_lineage.py::test_the_lineage_table_accounts_for_every_doc_source_field`
- The three groups' occupancy summed for the check → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/service.py::_field_loss_stats`
- The run-time field-loss check, against the tests input; a partial drop goes undetected → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/service.py::check_no_field_loss`
- A release view that drops every link reports no loss → `packages/services/normalize_tests/tests/test_service.py::test_in_the_release_view_dropping_every_link_raises_no_field_loss`
- The fixture against the golden, and the release view → `packages/services/normalize_tests/tests/test_service.py::test_the_command_writes_the_committed_fixture_golden`
- The built inputs → [test_builder.py](tests/test_builder.py)
- The utilities full samples → `packages/services/normalize_tests/tests/test_service.py::test_the_utilities_full_samples_pass_validation_and_lineage`
