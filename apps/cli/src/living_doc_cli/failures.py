# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The error lines and exit code of a command run that fails, shared by every command.
"""

import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager

from living_doc_core.input_validation import InputValidationError
from living_doc_utilities.contracts.codes import ContractError


@contextmanager
def exit_on_failure(logger: logging.Logger, command: str) -> Iterator[None]:
    """
    Run a command's service, and end a run that fails with exit code 1: one error line per input problem, or one for a
    contract error or an output that cannot be written.

    @param logger: The command's logger.
    @param command: The command's name, which starts the line for an output that cannot be written.
    """
    try:
        yield
    except InputValidationError as error:
        for problem in error.problems:
            logger.error("%s", problem)
        sys.exit(1)
    except ContractError as error:
        logger.error("%s", error)
        sys.exit(1)
    except OSError as error:
        logger.error("%s - the output cannot be written: %s", command, error)
        sys.exit(1)
