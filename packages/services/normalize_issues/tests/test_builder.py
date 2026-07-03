# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Unit tests for builder module.
"""

from living_doc_adapter_collector_gh.models import (
    AcceptanceCriterion,
    AdapterItem,
    AdapterItemTimestamps,
    AdapterMetadata,
    AdapterMetadataProducer,
    AdapterMetadataRun,
    AdapterMetadataSource,
    AdapterResult,
    CompatibilityWarning,
)

from living_doc_service_normalize_issues.builder import build_pdf_ready


def _make_metadata(
    *,
    build=None,
    run=None,
    repositories=None,
    organization=None,
    enterprise=None,
    original_metadata=None,
):
    """Build an AdapterMetadata with sensible defaults for tests."""
    return AdapterMetadata(
        producer=AdapterMetadataProducer(name="living-doc-collector-gh", version="1.0.0", build=build),
        run=run or AdapterMetadataRun(run_id=None, run_attempt=None, actor=None, workflow=None, ref=None, sha=None),
        source=AdapterMetadataSource(
            systems=["github"],
            repositories=repositories or ["github:owner/repo"],
            organization=organization,
            enterprise=enterprise,
        ),
        original_metadata=original_metadata if original_metadata is not None else {},
    )


def test_build_pdf_ready_basic():
    """Test basic PDF-ready building from adapter result."""
    item = AdapterItem(
        id="github:owner/repo#123",
        title="Test Issue",
        state="open",
        tags=["enhancement"],
        url="https://github.com/owner/repo/issues/123",
        timestamps=AdapterItemTimestamps(created="2026-01-01T00:00:00Z", updated="2026-01-02T00:00:00Z"),
        description="This is a test issue.",
    )

    metadata = _make_metadata(
        run=AdapterMetadataRun(
            run_id="123456", run_attempt="1", actor="testuser", workflow="test-workflow", ref="main", sha="abc123"
        ),
        organization="owner",
    )

    adapter_result = AdapterResult(user_stories=[item], metadata=metadata, warnings=[])

    options = {"document_title": "Test Document", "document_version": "1.0.0"}

    pdf_ready = build_pdf_ready(adapter_result, options)

    assert pdf_ready.schema_version == "1.0"
    assert pdf_ready.meta.document_title == "Test Document"
    assert pdf_ready.meta.document_version == "1.0.0"
    assert len(pdf_ready.content.user_stories) == 1

    story = pdf_ready.content.user_stories[0]
    assert story.id == "github:owner/repo#123"
    assert story.title == "Test Issue"
    assert story.state == "open"
    assert story.tags == ["enhancement"]
    assert story.url == "https://github.com/owner/repo/issues/123"
    assert story.timestamps.created == "2026-01-01T00:00:00Z"
    assert story.timestamps.updated == "2026-01-02T00:00:00Z"
    assert story.sections.description == "This is a test issue."


def test_build_pdf_ready_normalized_sections():
    """Test that structured sections are mapped correctly."""
    item = AdapterItem(
        id="github:owner/repo#456",
        title="Test Issue with Sections",
        state="open",
        tags=[],
        url="https://github.com/owner/repo/issues/456",
        timestamps=AdapterItemTimestamps(created="2026-01-01T00:00:00Z", updated="2026-01-01T00:00:00Z"),
        description="This is the overview.",
        business_value=["High value feature."],
        acceptance_criteria=[
            AcceptanceCriterion(id="GH-456-01", state="Active", version="v1.0.0", description="Criterion 1"),
            AcceptanceCriterion(id="GH-456-02", state="Active", version="v1.0.0", description="Criterion 2"),
        ],
    )

    metadata = _make_metadata(organization=None)

    adapter_result = AdapterResult(user_stories=[item], metadata=metadata, warnings=[])
    options = {}

    pdf_ready = build_pdf_ready(adapter_result, options)
    story = pdf_ready.content.user_stories[0]

    assert story.sections.description == "This is the overview."
    assert story.sections.business_value == ["High value feature."]
    assert story.sections.acceptance_criteria is not None
    assert any("Criterion 1" in ac.description for ac in story.sections.acceptance_criteria)
    assert any("Criterion 2" in ac.description for ac in story.sections.acceptance_criteria)


def test_build_pdf_ready_meta_fields():
    """Test that meta fields are populated correctly."""
    item = AdapterItem(
        id="github:owner/repo#1",
        title="Test",
        state="open",
        tags=[],
        url="https://github.com/owner/repo/issues/1",
        timestamps=AdapterItemTimestamps(created="2026-01-01T00:00:00Z", updated="2026-01-01T00:00:00Z"),
        description=None,
    )

    metadata = _make_metadata(repositories=["github:owner/repo1", "github:owner/repo2"])

    adapter_result = AdapterResult(user_stories=[item], metadata=metadata, warnings=[])
    options = {"document_title": "My Doc", "document_version": "2.0.0"}

    pdf_ready = build_pdf_ready(adapter_result, options)

    assert pdf_ready.meta.document_title == "My Doc"
    assert pdf_ready.meta.document_version == "2.0.0"
    assert pdf_ready.meta.generated_at is not None
    assert "T" in pdf_ready.meta.generated_at  # ISO 8601 format
    assert pdf_ready.meta.source_set == ["github:owner/repo1", "github:owner/repo2"]

    assert pdf_ready.meta.selection_summary.total_items == 1
    assert pdf_ready.meta.selection_summary.included_items == 1
    assert pdf_ready.meta.selection_summary.excluded_items == 0


def test_build_pdf_ready_fallback_document_title():
    """Test fallback document title when not provided."""
    item = AdapterItem(
        id="github:owner/repo#1",
        title="Test",
        state="open",
        tags=[],
        url="https://github.com/owner/repo/issues/1",
        timestamps=AdapterItemTimestamps(created="2026-01-01T00:00:00Z", updated="2026-01-01T00:00:00Z"),
        description=None,
    )

    metadata = _make_metadata(repositories=["github:owner/myrepo"])

    adapter_result = AdapterResult(user_stories=[item], metadata=metadata, warnings=[])
    options = {}  # No document_title provided

    pdf_ready = build_pdf_ready(adapter_result, options)

    assert "owner/myrepo" in pdf_ready.meta.document_title


def test_build_pdf_ready_audit_envelope():
    """Test that audit envelope is built correctly."""
    item = AdapterItem(
        id="github:owner/repo#1",
        title="Test",
        state="open",
        tags=[],
        url="https://github.com/owner/repo/issues/1",
        timestamps=AdapterItemTimestamps(created="2026-01-01T00:00:00Z", updated="2026-01-01T00:00:00Z"),
        description=None,
    )

    metadata = _make_metadata(
        build="build123",
        run=AdapterMetadataRun(
            run_id="123", run_attempt="1", actor="user1", workflow="workflow1", ref="main", sha="abc123"
        ),
        organization="myorg",
        enterprise="myenterprise",
        original_metadata={"some": "data"},
    )

    adapter_result = AdapterResult(user_stories=[item], metadata=metadata, warnings=[])
    options = {}

    pdf_ready = build_pdf_ready(adapter_result, options)
    audit = pdf_ready.meta.audit

    assert audit is not None
    assert audit.schema_version == "1.0"

    assert audit.producer.name == "living-doc-collector-gh"
    assert audit.producer.version == "1.0.0"
    assert audit.producer.build == "build123"

    assert audit.run.run_id == "123"
    assert audit.run.run_attempt == "1"
    assert audit.run.actor == "user1"
    assert audit.run.workflow == "workflow1"
    assert audit.run.ref == "main"
    assert audit.run.sha == "abc123"

    assert audit.source.systems == ["github"]
    assert audit.source.repositories == ["github:owner/repo"]
    assert audit.source.organization == "myorg"
    assert audit.source.enterprise == "myenterprise"

    assert "collector-gh" in audit.extensions
    assert audit.extensions["collector-gh"]["original_metadata"] == {"some": "data"}


def test_build_pdf_ready_audit_trace_normalization_step():
    """Test that normalization trace step is added."""
    item = AdapterItem(
        id="github:owner/repo#1",
        title="Test",
        state="open",
        tags=[],
        url="https://github.com/owner/repo/issues/1",
        timestamps=AdapterItemTimestamps(created="2026-01-01T00:00:00Z", updated="2026-01-01T00:00:00Z"),
        description=None,
    )

    metadata = _make_metadata()

    adapter_result = AdapterResult(user_stories=[item], metadata=metadata, warnings=[])
    options = {}

    pdf_ready = build_pdf_ready(adapter_result, options)
    audit = pdf_ready.meta.audit

    assert len(audit.trace) == 1
    trace_step = audit.trace[0]
    assert trace_step.step == "normalization"
    assert trace_step.tool == "living-doc-toolkit"
    assert trace_step.tool_version == "1.0.0"
    assert trace_step.started_at is not None
    assert trace_step.finished_at is not None


def test_build_pdf_ready_warnings_in_audit():
    """Test that adapter warnings are included in audit trace."""
    item = AdapterItem(
        id="github:owner/repo#1",
        title="Test",
        state="open",
        tags=[],
        url="https://github.com/owner/repo/issues/1",
        timestamps=AdapterItemTimestamps(created="2026-01-01T00:00:00Z", updated="2026-01-01T00:00:00Z"),
        description=None,
    )

    metadata = _make_metadata()

    warning = CompatibilityWarning(code="VERSION_MISMATCH", message="Version mismatch detected", context="v0.9.0")

    adapter_result = AdapterResult(user_stories=[item], metadata=metadata, warnings=[warning])
    options = {}

    pdf_ready = build_pdf_ready(adapter_result, options)
    audit = pdf_ready.meta.audit

    trace_step = audit.trace[0]
    assert len(trace_step.warnings) == 1
    assert trace_step.warnings[0].code == "VERSION_MISMATCH"
    assert trace_step.warnings[0].message == "Version mismatch detected"
    assert trace_step.warnings[0].context == "v0.9.0"


def test_build_pdf_ready_run_context():
    """Test that run context is populated when run data is available."""
    item = AdapterItem(
        id="github:owner/repo#1",
        title="Test",
        state="open",
        tags=[],
        url="https://github.com/owner/repo/issues/1",
        timestamps=AdapterItemTimestamps(created="2026-01-01T00:00:00Z", updated="2026-01-01T00:00:00Z"),
        description=None,
    )

    metadata = _make_metadata(
        run=AdapterMetadataRun(
            run_id="789", run_attempt="2", actor="testuser", workflow="ci", ref="feature-branch", sha="def456"
        ),
    )

    adapter_result = AdapterResult(user_stories=[item], metadata=metadata, warnings=[])
    options = {}

    pdf_ready = build_pdf_ready(adapter_result, options)

    assert pdf_ready.meta.run_context is not None
    assert pdf_ready.meta.run_context.ci_run_id == "789"
    assert pdf_ready.meta.run_context.triggered_by == "testuser"
    assert pdf_ready.meta.run_context.branch == "feature-branch"
    assert pdf_ready.meta.run_context.commit_sha == "def456"


def test_build_pdf_ready_multiple_items():
    """Test building PDF-ready with multiple items."""
    items = [
        AdapterItem(
            id=f"github:owner/repo#{i}",
            title=f"Issue {i}",
            state="open",
            tags=["tag1"],
            url=f"https://github.com/owner/repo/issues/{i}",
            timestamps=AdapterItemTimestamps(created="2026-01-01T00:00:00Z", updated="2026-01-01T00:00:00Z"),
            description=f"Issue {i} content.",
        )
        for i in range(1, 6)
    ]

    metadata = _make_metadata()

    adapter_result = AdapterResult(user_stories=items, metadata=metadata, warnings=[])
    options = {}

    pdf_ready = build_pdf_ready(adapter_result, options)

    assert len(pdf_ready.content.user_stories) == 5
    assert pdf_ready.meta.selection_summary.total_items == 5
    assert pdf_ready.meta.selection_summary.included_items == 5

    for i, story in enumerate(pdf_ready.content.user_stories, start=1):
        assert story.id == f"github:owner/repo#{i}"
        assert story.title == f"Issue {i}"
        assert story.sections.description == f"Issue {i} content."
