# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""The `normalize-tests` lineage table: each input scenario path maps to its User Story group twin."""

from living_doc_utilities.contracts.lineage import LineageTable

USER_STORY_SCENARIO_ROOT = "feature_files[].linked_to_user_story[].scenarios[]."
FUNCTIONALITY_SCENARIO_ROOT = "feature_files[].linked_to_functionality[].scenarios[]."
UNLINKED_SCENARIO_ROOT = "feature_files[].unlinked[]."

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

LINEAGE_TABLE = LineageTable({f"scenarios[].{path}": f"{USER_STORY_SCENARIO_ROOT}{path}" for path in SCENARIO_PATHS})
