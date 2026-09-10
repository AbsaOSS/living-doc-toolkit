# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Generator-ready JSON builder for normalized issues.

This module builds GeneratorReadyV1 objects from AdapterResult data with normalized sections.
"""

from datetime import datetime, timezone

from living_doc_adapter_collector_gh.models import AdapterResult  # type: ignore[import-untyped]
from living_doc_datasets_generator_ready.audit.v1.models import (  # type: ignore[import-untyped]
    AuditEnvelopeV1,
    AuditWarning,
    Producer,
    Run,
    Source,
    TraceStep,
)
from living_doc_datasets_generator_ready.generator_ready.v1.models import (  # type: ignore[import-untyped]
    AcceptanceCriterion,
    Content,
    GeneratorReadyV1,
    Meta,
    RunContext,
    Sections,
    SelectionSummary,
    Timestamps,
    UserStory,
    ViewSummary,
)

# Content view filtering (see docs/contracts.md "Content Views"). The ``release`` view
# hides work that is not yet public; the ``inner`` view keeps everything.
DROP_ENTITY_STATES = frozenset({"planned", "in_review"})
# ``deprecated`` ACs are kept: they describe behaviour that shipped and is still part of the
# solution. Only not-yet-real ACs (``planned`` / ``in_review``) are release-hidden.
DROP_AC_STATES = frozenset({"planned", "in_review"})


def _normalize_state(state: str | None) -> str:
    """Fold a free-form state label to its canonical comparison form (e.g. 'In Review' -> 'in_review')."""
    return (state or "").strip().lower().replace(" ", "_").replace("-", "_")


def build_generator_ready(adapter_result: AdapterResult, options: dict) -> GeneratorReadyV1:
    """
    Build generator-ready JSON from adapter result.

    This function transforms AdapterResult into GeneratorReadyV1 format from the structured
    item fields, populating metadata, and building the audit trail.

    Args:
        adapter_result: Parsed adapter result with items and metadata
        options: Configuration options (document_title, document_version, etc.)

    Returns:
        GeneratorReadyV1 object ready for serialization
    """
    # pylint: disable=too-many-locals
    view = options.get("view", "inner")
    release_view = view == "release"

    # Build output user stories from the adapter's parsed items
    user_stories = []
    filtered_user_stories = 0
    filtered_acceptance_criteria = 0
    for item in adapter_result.items:
        if release_view and _normalize_state(item.state) in DROP_ENTITY_STATES:
            filtered_user_stories += 1
            continue

        acceptance_criteria: list[AcceptanceCriterion] | None = None
        if item.acceptance_criteria is not None:
            source_acs = item.acceptance_criteria
            if release_view:
                kept_acs = [ac for ac in source_acs if _normalize_state(ac.state) not in DROP_AC_STATES]
                filtered_acceptance_criteria += len(source_acs) - len(kept_acs)
                source_acs = kept_acs
            acceptance_criteria = [
                AcceptanceCriterion(
                    id=ac.id,
                    state=ac.state,
                    version=ac.version,
                    description=ac.description,
                )
                for ac in source_acs
            ]

        # Build Sections object from structured fields
        sections = Sections(
            description=item.description,
            business_value=item.business_value,
            preconditions=item.preconditions,
            acceptance_criteria=acceptance_criteria,
            user_guide=None,
            connections=None,
            last_edited=None,
        )

        # Build UserStory object
        user_story = UserStory(
            id=item.id,
            title=item.title,
            state=item.state,
            tags=item.tags,
            url=item.url,
            timestamps=Timestamps(
                created=item.timestamps.created,
                updated=item.timestamps.updated,
            ),
            sections=sections,
        )
        user_stories.append(user_story)

    # Build Content
    content = Content(user_stories=user_stories)

    # Build SelectionSummary
    total_items = len(adapter_result.items)
    included_items = len(user_stories)
    selection_summary = SelectionSummary(
        total_items=total_items,
        included_items=included_items,
        excluded_items=total_items - included_items,
    )

    # Record the applied view and how much content it filtered out
    view_summary = ViewSummary(
        view=view,
        filtered_user_stories=filtered_user_stories,
        filtered_acceptance_criteria=filtered_acceptance_criteria,
    )

    # Build source_set from adapter metadata
    source_set = []
    for repo in adapter_result.metadata.source.repositories:
        # Format repositories with github: prefix for source_set
        if not repo.startswith("github:"):
            source_set.append(f"github:{repo}")
        else:
            source_set.append(repo)

    # Fallback for document_title if not provided
    document_title = options.get("document_title")
    if not document_title:
        # Derive from first repository if available
        if source_set:
            # Extract repo name from github:owner/repo format
            first_repo = source_set[0].replace("github:", "")
            document_title = f"Living Documentation - {first_repo}"
        else:
            document_title = "Living Documentation"

    # Get document_version with fallback
    document_version = options.get("document_version", "1.0.0")

    # Build RunContext if available
    run_context = None
    if adapter_result.metadata.run.run_id:
        run_context = RunContext(
            ci_run_id=adapter_result.metadata.run.run_id,
            triggered_by=adapter_result.metadata.run.actor,
            branch=adapter_result.metadata.run.ref,
            commit_sha=adapter_result.metadata.run.sha,
        )

    # Build audit envelope
    audit = _build_audit_envelope(adapter_result, options)

    # Get current timestamp
    generated_at = datetime.now(timezone.utc).isoformat()

    # Build Meta
    meta = Meta(
        document_title=document_title,
        document_version=document_version,
        generated_at=generated_at,
        source_set=source_set,
        selection_summary=selection_summary,
        view=view_summary,
        run_context=run_context,
        audit=audit,
    )

    # Build GeneratorReadyV1
    generator_ready = GeneratorReadyV1(schema_version="generator-ready-v1.0.0", meta=meta, content=content)

    return generator_ready


def _build_audit_envelope(adapter_result: AdapterResult, _options: dict) -> AuditEnvelopeV1:
    """
    Build audit envelope from adapter metadata.

    Maps adapter metadata to audit envelope structure and adds normalization trace step.

    Args:
        adapter_result: Adapter result with metadata
        options: Configuration options (currently unused)

    Returns:
        AuditEnvelopeV1 object
    """
    # Map producer metadata
    producer = Producer(
        name=adapter_result.metadata.producer.name,
        version=adapter_result.metadata.producer.version,
        build=adapter_result.metadata.producer.build,
    )

    # Map run metadata
    run = Run(
        run_id=adapter_result.metadata.run.run_id,
        run_attempt=adapter_result.metadata.run.run_attempt,
        actor=adapter_result.metadata.run.actor,
        workflow=adapter_result.metadata.run.workflow,
        ref=adapter_result.metadata.run.ref,
        sha=adapter_result.metadata.run.sha,
    )

    # Map source metadata
    source = Source(
        systems=adapter_result.metadata.source.systems,
        repositories=adapter_result.metadata.source.repositories,
        organization=adapter_result.metadata.source.organization,
        enterprise=adapter_result.metadata.source.enterprise,
    )

    # Build trace with normalization step
    now = datetime.now(timezone.utc).isoformat()

    # Convert adapter warnings to audit warnings
    audit_warnings = [AuditWarning(code=w.code, message=w.message, context=w.context) for w in adapter_result.warnings]

    normalization_step = TraceStep(
        step="normalization",
        tool="living-doc-toolkit",
        tool_version="1.0.0",
        started_at=now,
        finished_at=now,
        warnings=audit_warnings,
    )

    trace = [normalization_step]

    # Build extensions with original metadata
    extensions = {"collector-gh": {"original_metadata": adapter_result.metadata.original_metadata}}

    # Build audit envelope
    audit = AuditEnvelopeV1(
        schema_version="1.0",
        producer=producer,
        run=run,
        source=source,
        trace=trace,
        extensions=extensions,
    )

    return audit
