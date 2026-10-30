# living-doc-service-normalize-tests

Parent: `../CONTEXT.md`

The `normalize-tests` transform. Its behaviour is [README.md](README.md); this file maps that page to the code.

## Code map

What realises each fact of [README.md](README.md):

- Both files are `living-doc-utilities` contracts; no copy here → utilities
- A run's four steps; nothing written when one fails → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/service.py::normalize_tests`
- Grouping by feature file and linked entity, the order, unlinked scenarios, the envelope, forwarded warnings → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/builder.py::build_ui_test_catalog`
- A feature file's key and name → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/builder.py::_feature_file`
- The repository-qualified name relies on the collector's `scenario_id` shape → collector-gh
- A link's entity id, once per entity → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/builder.py::_entity_ids`
- The lineage table → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/lineage.py::LINEAGE_TABLE`
- The table is complete against `ui-tests-v1.0.0` → `packages/services/normalize_tests/tests/test_lineage.py::test_the_lineage_table_accounts_for_every_ui_tests_field`
- The three groups' occupancy summed for the check → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/service.py::_field_loss_stats`
- The run-time field-loss check; a partial drop goes undetected → `packages/services/normalize_tests/src/living_doc_service_normalize_tests/service.py::check_no_field_loss`
- The fixture against the golden → `packages/services/normalize_tests/tests/test_service.py::test_the_command_writes_the_committed_fixture_golden`
- The built inputs → [test_builder.py](tests/test_builder.py)
- The utilities full sample → `packages/services/normalize_tests/tests/test_service.py::test_the_utilities_full_sample_passes_validation_and_lineage`
