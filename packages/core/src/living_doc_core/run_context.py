# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The CI run context a command records in its output's `metadata.run`: the GitHub Actions run the file is written in,
audit only (`living-doc-utilities` `docs/contracts/artifact-rules.md` § The metadata envelope).
"""

import os

from living_doc_utilities.contracts.envelope import Run

# Each `Run` field, with the GitHub Actions variable that holds it.
RUN_VARIABLES = {
    "run_id": "GITHUB_RUN_ID",
    "run_attempt": "GITHUB_RUN_ATTEMPT",
    "actor": "GITHUB_ACTOR",
    "workflow": "GITHUB_WORKFLOW",
    "ref": "GITHUB_REF",
    "sha": "GITHUB_SHA",
}


def run_context() -> Run:
    """
    Read the CI run context from the environment.

    @return: The run. A field whose variable is unset or empty is `None`, so outside GitHub Actions every field is.
    """
    return Run.model_validate({field: os.environ.get(variable) or None for field, variable in RUN_VARIABLES.items()})
