# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The `normalize-docs` lineage table (R11): every `doc-source-v1.0.0` field path and the `generator-ready-v1.0.0` path
it becomes. The builder concatenates the three entity lists onto `content.entities[]` without translating a field, so
each list's path maps to the same path under `content.entities[]`, and none is dropped.
"""

from living_doc_utilities.contracts.lineage import LineageTable

# The input's entity lists; each holds the same entity shape.
INPUT_ROOTS = ("user_stories", "features", "functionalities")
OUTPUT_ROOT = "content.entities"

# Every field path of one entity, relative to its list, in the model's field order. Declared here, not read from the
# contract, so a field a later contract version adds fails `assert_complete` in this package's tests until it is added.
ENTITY_PATHS = (
    "entity_id",
    "source_ref.system",
    "source_ref.native_id",
    "source_ref.native_type",
    "source_ref.url",
    "source_ref.tracker_state",
    "source_ref.area_path",
    "source_ref.iteration_path",
    "type",
    "title",
    "state",
    "state_origin",
    "tags[]",
    "timestamps.created_at",
    "timestamps.updated_at",
    "timestamps.closed_at",
    "narrative",
    "purpose",
    "source",
    "notes[]",
    "business_value[]",
    "acceptance_criteria[].id",
    "acceptance_criteria[].state",
    "acceptance_criteria[].version",
    "acceptance_criteria[].description",
    "acceptance_criteria[].aspect[]",
    "acceptance_criteria[].preconditions[]",
    "acceptance_criteria[].not_in_scope[]",
    "acceptance_criteria[].removal_planned",
    "acceptance_criteria[].rationale",
    "acceptance_criteria[].placeholder_values",
    "preconditions[]",
    "not_in_scope[]",
    "deprecated_at",
    "deprecation_reason",
    "superseded_by",
    "surface_type",
    "owners[]",
    "user_stories[]",
    "functionalities[]",
    "external_dependencies[]",
    "feature_dependencies[]",
    "stub_reason",
    "wizard_steps[]",
    "pages[].is_primary",
    "pages[].route",
    "pages[].page_object",
    "pages[].owners[]",
    "pages[].purpose",
    "pages[].functionalities[]",
    "pages[].notes[]",
    "parent",
    "func_type",
    "rationale",
)

LINEAGE_TABLE = LineageTable(
    {f"{root}[].{path}": f"{OUTPUT_ROOT}[].{path}" for root in INPUT_ROOTS for path in ENTITY_PATHS}
)
