# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
PDF-ready JSON builder for normalized issues.

This module builds PdfReadyV1 objects from AdapterResult data with normalized sections.
"""

from datetime import datetime, timezone

from living_doc_adapter_collector_gh.models import AdapterResult  # type: ignore[import-untyped]
from living_doc_datasets_pdf.audit.v1.models import (  # type: ignore[import-untyped]
    AuditEnvelopeV1,
    AuditWarning,
    Producer,
    Run,
    Source,
    TraceStep,
)
from living_doc_datasets_pdf.pdf_ready.v1.models import (  # type: ignore[import-untyped]
    Content,
    Meta,
    PdfReadyV1,
    RunContext,
    Sections,
    SelectionSummary,
    Timestamps,
    UserStory,
)

from living_doc_service_normalize_issues.normalizer import normalize_sections


def build_pdf_ready(adapter_result: AdapterResult, options: dict) -> PdfReadyV1:  # pylint: disable=too-many-locals
    """
    Build PDF-ready JSON from adapter result.

    This function transforms AdapterResult into PdfReadyV1 format, normalizing markdown
    sections, populating metadata, and building the audit trail.

    Args:
        adapter_result: Parsed adapter result with items and metadata
        options: Configuration options (document_title, document_version, etc.)

    Returns:
        PdfReadyV1 object ready for serialization
    """
    # Build user stories from adapter items
    user_stories = []
    for item in adapter_result.items:
        # Normalize markdown sections
        normalized = normalize_sections(item.body or "")

        # Build Sections object
        sections = Sections(
            description=normalized.get("description"),
            business_value=normalized.get("business_value"),
            preconditions=normalized.get("preconditions"),
            acceptance_criteria=normalized.get("acceptance_criteria"),
            user_guide=normalized.get("user_guide"),
            connections=normalized.get("connections"),
            last_edited=normalized.get("last_edited"),
        )

        # Build UserStory object
        user_story = UserStory(
            id=item.id,
            title=item.title,
            state=item.state,
            tags=item.tags,
            url=item.url,
            timestamps=Timestamps(created=item.timestamps.created, updated=item.timestamps.updated),
            sections=sections,
        )
        user_stories.append(user_story)

    # Build Content
    content = Content(user_stories=user_stories)

    # Build SelectionSummary
    total_items = len(adapter_result.items)
    selection_summary = SelectionSummary(
        total_items=total_items, included_items=total_items, excluded_items=0
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
        run_context=run_context,
        audit=audit,
    )

    # Build PdfReadyV1
    pdf_ready = PdfReadyV1(schema_version="1.0", meta=meta, content=content)

    return pdf_ready


def _build_audit_envelope(adapter_result: AdapterResult, options: dict) -> AuditEnvelopeV1:  # pylint: disable=unused-argument
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
    audit_warnings = []
    for warning in adapter_result.warnings:
        audit_warnings.append(
            AuditWarning(code=warning.code, message=warning.message, context=warning.context)
        )

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
