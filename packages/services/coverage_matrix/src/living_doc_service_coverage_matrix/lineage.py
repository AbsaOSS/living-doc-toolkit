# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The `coverage-matrix` lineage table (R11), one table over both inputs: every `doc-source-v1.0.0` and every
`ui-tests-v1.0.0` field path, each mapped to the `coverage-matrix-v1.0.0` path it becomes or dropped with its reason.
"""

from living_doc_utilities.contracts.lineage import Dropped, LineageEntry, LineageTable

# The documentation lists the matrix reads; each holds the same entity shape, and each becomes `entities[]`.
COUNTED_ROOTS = ("user_stories", "functionalities")
FEATURE_ROOT = "features"
ENTITY_ROOT = "entities[]."
ROW_ROOT = "entities[].acceptance_criteria[]."

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

# The entity paths a User Story or Functionality carries into the matrix, and where.
MAPPED_ENTITY_PATHS = {
    "entity_id": f"{ENTITY_ROOT}entity_id",
    "type": f"{ENTITY_ROOT}type",
    "title": f"{ENTITY_ROOT}title",
    "state": f"{ENTITY_ROOT}state",
    "acceptance_criteria[].id": f"{ROW_ROOT}ac_id",
    "acceptance_criteria[].state": f"{ROW_ROOT}state",
    "acceptance_criteria[].aspect[]": f"{ROW_ROOT}aspects[].aspect",
    "acceptance_criteria[].placeholder_values": f"{ROW_ROOT}keyword",
}

# Every field path of one scenario, relative to `scenarios[]`, in the model's field order.
SCENARIO_PATHS = (
    "scenario_id",
    "title",
    "source_ref.system",
    "source_ref.native_id",
    "source_ref.native_type",
    "source_ref.url",
    "source_ref.tracker_state",
    "source_ref.area_path",
    "source_ref.iteration_path",
    "tags[]",
    "acceptance_criteria[].id",
    "acceptance_criteria[].aspect",
)

NO_FEATURE_ROW = Dropped(
    "the coverage matrix has no Feature entity: it counts the acceptance criteria of User Stories and Functionalities"
)
NOT_CONTENT = Dropped("the coverage matrix carries coverage, not the documentation's content")
LINK_ROUTES_SCENARIO = Dropped(
    "a link decides which criterion's row lists its scenario; the row's ac_id comes from the documentation input"
)
LINK_ROUTES_ASPECT = Dropped(
    "a link's aspect decides which aspect of the criterion's row lists its scenario; the row's aspects come from the "
    "documentation input"
)
SCENARIO_BY_ID = Dropped("a coverage row names its scenarios by scenario_id only")


def _entity_entry(path: str) -> LineageEntry:
    return MAPPED_ENTITY_PATHS.get(path, NOT_CONTENT)


def _scenario_entry(path: str) -> LineageEntry:
    if path == "scenario_id":
        return f"{ROW_ROOT}scenario_ids[]"
    if path == "acceptance_criteria[].id":
        return LINK_ROUTES_SCENARIO
    if path == "acceptance_criteria[].aspect":
        return LINK_ROUTES_ASPECT
    return SCENARIO_BY_ID


LINEAGE_TABLE = LineageTable(
    {
        **{f"{root}[].{path}": _entity_entry(path) for root in COUNTED_ROOTS for path in ENTITY_PATHS},
        **{f"{FEATURE_ROOT}[].{path}": NO_FEATURE_ROW for path in ENTITY_PATHS},
        **{f"scenarios[].{path}": _scenario_entry(path) for path in SCENARIO_PATHS},
    }
)
