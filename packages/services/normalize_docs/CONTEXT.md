# living-doc-service-normalize-docs

Parent: `../CONTEXT.md`

The `normalize-docs` transform. Its behaviour is [README.md](README.md); this file maps that page to the code.

## Code map

What realises each fact of [README.md](README.md):

- Both files are `living-doc-utilities` contracts; no copy here → utilities
- A run's four steps; nothing written when one fails → `packages/services/normalize_docs/src/living_doc_service_normalize_docs/service.py::normalize_docs`
- The three entity lists, concatenated in order → `packages/services/normalize_docs/src/living_doc_service_normalize_docs/builder.py::_entity_lists`
- The view filter, once per list; the document block; the envelope; forwarded warnings → `packages/services/normalize_docs/src/living_doc_service_normalize_docs/builder.py::build_generator_ready`
- `document.selection_summary` sums the three lists' counts → `packages/services/normalize_docs/src/living_doc_service_normalize_docs/builder.py::_summed`
- The default document version, `1.0.0` → `packages/services/normalize_docs/src/living_doc_service_normalize_docs/builder.py::DEFAULT_DOCUMENT_VERSION`
- The action passes no document version → `main.py::COMMAND_INPUTS`
- The lineage table → `packages/services/normalize_docs/src/living_doc_service_normalize_docs/lineage.py::LINEAGE_TABLE`
- The 54 entity paths → `packages/services/normalize_docs/src/living_doc_service_normalize_docs/lineage.py::ENTITY_PATHS`
- The table is complete against `doc-source-v1.0.0` → `packages/services/normalize_docs/tests/test_lineage.py::test_the_table_accounts_for_every_doc_source_path`
- A field the table does not know never stops a run → `packages/services/normalize_docs/tests/test_lineage.py::test_a_field_the_table_does_not_know_never_stops_a_run`
- The run-time field-loss check against `selected_stats` → `packages/services/normalize_docs/src/living_doc_service_normalize_docs/service.py::check_no_field_loss`
- R12 check 3, the full sample in both views → `packages/services/normalize_docs/tests/test_full_sample.py::test_the_full_sample_loses_no_field_in_either_view`
- The fixture against the goldens → `packages/services/normalize_docs/tests/test_service.py::test_over_the_fixture_the_command_writes_the_committed_golden`
- Each named authored field and the six golden entities → `packages/services/normalize_docs/tests/test_authored_fields.py::test_every_authored_field_of_each_golden_entity_reaches_the_inner_output`
