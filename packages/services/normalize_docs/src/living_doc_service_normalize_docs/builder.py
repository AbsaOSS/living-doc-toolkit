# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
The `normalize-docs` builder: a documentation input's contract model to the `generator-ready` contract model. It
reads and writes no file; `service` does.
"""

from collections import Counter
from collections.abc import Iterable
from datetime import datetime
from importlib.metadata import version as installed_version

from living_doc_core.views import select_records
from living_doc_utilities.contracts import doc_source
from living_doc_utilities.contracts.common import View
from living_doc_utilities.contracts.compat import installed_utilities_version
from living_doc_utilities.contracts.doc_entities import Entity
from living_doc_utilities.contracts.doc_source import DocSourceResult
from living_doc_utilities.contracts.envelope import (
    AuditStats,
    Cardinality,
    ContractWarning,
    Metadata,
    Producer,
    SourceInputEntry,
    Stats,
)
from living_doc_utilities.contracts.generator_ready import Content, Document, GeneratorReadyResult, SelectionSummary
from living_doc_utilities.contracts.stats import compute_stats

PRODUCER_NAME = "AbsaOSS/living-doc-toolkit"
# The toolkit has one version, the action's release: every package declares it, and `living-doc-core`'s is read.
TOOLKIT_VERSION = installed_version("living-doc-core")
DEFAULT_DOCUMENT_VERSION = "1.0.0"


def _entity_lists(documentation: DocSourceResult) -> dict[str, list[Entity]]:
    """The input's entity lists, in the order `content.entities[]` concatenates them: the canon's entity-type order."""
    return {
        "user_stories": documentation.user_stories,
        "features": documentation.features,
        "functionalities": documentation.functionalities,
    }


def _summed(summaries: Iterable[SelectionSummary]) -> SelectionSummary:
    """The lists' selection counts, added up."""
    total: Counter[str] = Counter()
    for summary in summaries:
        total.update(summary.model_dump())
    return SelectionSummary.model_validate(total)


def forwarded(warning: ContractWarning, source: str) -> ContractWarning:
    """
    An input warning as the output carries it: unchanged but for `context`, which names the input first and keeps the
    warning's own context after it, as `input='<contract id>' <context>`.

    @param warning: The input's warning.
    @param source: The input's contract id, its `schema_version`. A run reads one input per contract, and its
        `metadata.source_inputs[]` entry carries the same id, so the name points into the output itself.
    @return: A copy of the warning.
    """
    named = f"input={source!r}"
    return warning.model_copy(update={"context": f"{named} {warning.context}" if warning.context else named})


def build_generator_ready(
    documentation: DocSourceResult,
    *,
    view: View,
    generated_at: datetime,
    title: str | None = None,
    version: str | None = None,
) -> GeneratorReadyResult:
    """
    Build `generator-ready` from one documentation input: the records the view keeps, every authored field carried as
    it is, the input's warnings forwarded and the input recorded in `metadata.source_inputs[]`.

    @param documentation: The validated documentation input.
    @param view: The view the output holds, `inner` or `release`.
    @param generated_at: The write time.
    @param title: `document.title`; the input's `metadata.source.project_id` when not given.
    @param version: `document.version`; `DEFAULT_DOCUMENT_VERSION` when not given.
    @return: The output model. Its `metadata.stats` holds only the counts a caller reports, all 0 for a transform, and
        `write_artifact` computes the rest.
    """
    selections = {name: select_records(entities, view) for name, entities in _entity_lists(documentation).items()}
    kept_input = documentation.model_copy(update={name: kept for name, (kept, _) in selections.items()})
    selected = compute_stats(kept_input, doc_source.RECORD_ROOTS, documentation.metadata.stats.cardinality)
    source = documentation.metadata.source

    return GeneratorReadyResult(
        metadata=Metadata(
            producer=Producer(
                name=PRODUCER_NAME, version=TOOLKIT_VERSION, utilities_version=installed_utilities_version()
            ),
            source=source,
            generated_at=generated_at,
            stats=Stats(cardinality=Cardinality()),
            source_inputs=[
                SourceInputEntry(
                    schema_version=documentation.schema_version,
                    producer=documentation.metadata.producer,
                    run=documentation.metadata.run,
                    source=source,
                    stats=AuditStats.model_validate(documentation.metadata.stats.model_dump()),
                    selected_stats=AuditStats.model_validate(selected.model_dump()),
                )
            ],
        ),
        warnings=[forwarded(warning, documentation.schema_version) for warning in documentation.warnings],
        document=Document(
            view=view,
            title=title or source.project_id,
            version=version or DEFAULT_DOCUMENT_VERSION,
            selection_summary=_summed(summary for _, summary in selections.values()),
        ),
        content=Content(entities=[entity for kept, _ in selections.values() for entity in kept]),
    )
