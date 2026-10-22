# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""The toolkit producer identity and shared warning forwarding."""

from importlib.metadata import version as installed_version

from living_doc_utilities.contracts.envelope import ContractWarning

PRODUCER_NAME = "AbsaOSS/living-doc-toolkit"
TOOLKIT_VERSION = installed_version("living-doc-core")


def forwarded(warning: ContractWarning, source: str) -> ContractWarning:
    """Copy an input warning, naming its contract before retaining any existing context."""
    named = f"source_input={source!r}"
    return warning.model_copy(update={"context": f"{named} {warning.context}" if warning.context else named})
