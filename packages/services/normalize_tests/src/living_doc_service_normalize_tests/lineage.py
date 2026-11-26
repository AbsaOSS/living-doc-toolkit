# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The `normalize-tests` lineage table (R11), one table over both inputs: each `ui-tests-v1.0.0` scenario path maps to
its User Story group twin, a file's background to its feature file, and of the `doc-source-v1.0.0` paths only a
criterion's state, onto the links to it.
"""

from living_doc_utilities.contracts.lineage import Dropped, LineageEntry, LineageTable

USER_STORY_SCENARIO_ROOT = "feature_files[].linked_to_user_story[].scenarios[]."
FUNCTIONALITY_SCENARIO_ROOT = "feature_files[].linked_to_functionality[].scenarios[]."
UNLINKED_SCENARIO_ROOT = "feature_files[].unlinked[]."
FEATURE_FILE_BACKGROUND = "feature_files[].background[]"

# Every field path of one scenario the catalog carries on its scenario, relative to `scenarios[]`. Declared here, not
# read from the contract, so a field a later contract version adds fails `assert_complete` in this package's tests.
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
    "line",
    "rule",
    "rule_background[]",
    "steps[]",
    "acceptance_criteria[].id",
    "acceptance_criteria[].aspect",
)

# The documentation's entity lists, and those whose criteria a scenario can link (`AC_ID_PATTERN`).
DOCUMENTATION_ROOTS = ("user_stories", "features", "functionalities")
CRITERIA_ROOTS = ("user_stories", "functionalities")
CRITERION_STATE = "acceptance_criteria[].state"

# Every field path of one documentation entity, relative to its list, in the model's field order.
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

STATES_ONLY = Dropped(
    "the catalog carries the tests input's scenarios; it reads only the state of each criterion a scenario can link, "
    "a User Story's or a Functionality's"
)


def _documentation_entry(root: str, path: str) -> LineageEntry:
    if root in CRITERIA_ROOTS and path == CRITERION_STATE:
        return f"{USER_STORY_SCENARIO_ROOT}{CRITERION_STATE}"
    return STATES_ONLY


LINEAGE_TABLE = LineageTable(
    {
        **{f"scenarios[].{path}": f"{USER_STORY_SCENARIO_ROOT}{path}" for path in SCENARIO_PATHS},
        "scenarios[].background[]": FEATURE_FILE_BACKGROUND,
        **{
            f"{root}[].{path}": _documentation_entry(root, path)
            for root in DOCUMENTATION_ROOTS
            for path in ENTITY_PATHS
        },
    }
)
