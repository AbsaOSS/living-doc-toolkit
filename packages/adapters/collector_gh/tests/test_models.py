# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for the models module."""

import pytest
from pydantic import ValidationError

from living_doc_adapter_collector_gh.models import (
    AdapterItem,
    AdapterItemTimestamps,
    AdapterMetadata,
    AdapterMetadataProducer,
    AdapterMetadataRun,
    AdapterMetadataSource,
    AdapterResult,
    CompatibilityWarning,
)


class TestCompatibilityWarning:
    """Tests for the CompatibilityWarning model."""

    def test_create_with_all_fields(self):
        """Test creating CompatibilityWarning with all fields."""
        warning = CompatibilityWarning(code="VERSION_MISMATCH", message="Test message", context="test.context")
        assert warning.code == "VERSION_MISMATCH"
        assert warning.message == "Test message"
        assert warning.context == "test.context"

    def test_create_without_context(self):
        """Test creating CompatibilityWarning without context field."""
        warning = CompatibilityWarning(code="TEST_CODE", message="Test message")
        assert warning.code == "TEST_CODE"
        assert warning.message == "Test message"
        assert warning.context is None


class TestAdapterItemTimestamps:
    """Tests for the AdapterItemTimestamps model."""

    def test_create_timestamps(self):
        """Test creating AdapterItemTimestamps."""
        timestamps = AdapterItemTimestamps(created="2026-01-01T00:00:00Z", updated="2026-01-02T00:00:00Z")
        assert timestamps.created == "2026-01-01T00:00:00Z"
        assert timestamps.updated == "2026-01-02T00:00:00Z"


class TestAdapterItem:
    """Tests for the AdapterItem model."""

    def test_create_with_all_fields(self):
        """Test creating AdapterItem with all fields."""
        item = AdapterItem(
            id="github:owner/repo#42",
            title="Test Issue",
            state="open",
            tags=["tag1", "tag2"],
            url="https://github.com/owner/repo/issues/42",
            timestamps=AdapterItemTimestamps(created="2026-01-01T00:00:00Z", updated="2026-01-02T00:00:00Z"),
            body="Issue body content",
        )
        assert item.id == "github:owner/repo#42"
        assert item.title == "Test Issue"
        assert item.state == "open"
        assert item.tags == ["tag1", "tag2"]
        assert item.body == "Issue body content"

    def test_create_without_body(self):
        """Test creating AdapterItem without body field."""
        item = AdapterItem(
            id="github:owner/repo#42",
            title="Test Issue",
            state="open",
            tags=[],
            url="https://github.com/owner/repo/issues/42",
            timestamps=AdapterItemTimestamps(created="2026-01-01T00:00:00Z", updated="2026-01-02T00:00:00Z"),
        )
        assert item.body is None

    def test_create_with_empty_tags(self):
        """Test creating AdapterItem with empty tags list."""
        item = AdapterItem(
            id="github:owner/repo#1",
            title="No Tags",
            state="closed",
            tags=[],
            url="https://github.com/owner/repo/issues/1",
            timestamps=AdapterItemTimestamps(created="2026-01-01T00:00:00Z", updated="2026-01-02T00:00:00Z"),
        )
        assert item.tags == []

    def test_validation_fails_with_missing_required_field(self):
        """Test that validation fails when required field is missing."""
        with pytest.raises(ValidationError):
            AdapterItem(
                id="github:owner/repo#1",
                # Missing title
                state="open",
                tags=[],
                url="https://github.com/owner/repo/issues/1",
                timestamps=AdapterItemTimestamps(created="2026-01-01T00:00:00Z", updated="2026-01-02T00:00:00Z"),
            )


class TestAdapterMetadata:
    """Tests for the AdapterMetadata model."""

    def test_create_metadata(self):
        """Test creating AdapterMetadata."""
        metadata = AdapterMetadata(
            producer=AdapterMetadataProducer(name="test-producer", version="1.0.0", build="abc123"),
            run=AdapterMetadataRun(
                run_id="123",
                run_attempt="1",
                actor="user@example.com",
                workflow="test-workflow",
                ref="refs/heads/main",
                sha="abc123",
            ),
            source=AdapterMetadataSource(
                systems=["GitHub"], repositories=["owner/repo"], organization="owner", enterprise=None
            ),
            original_metadata={"test": "data"},
        )
        assert metadata.producer.name == "test-producer"
        assert metadata.run.run_id == "123"
        assert metadata.source.systems == ["GitHub"]
        assert metadata.original_metadata == {"test": "data"}


class TestAdapterResult:
    """Tests for the AdapterResult model."""

    def test_create_result_with_items_and_warnings(self):
        """Test creating AdapterResult with items and warnings."""
        result = AdapterResult(
            items=[
                AdapterItem(
                    id="github:owner/repo#1",
                    title="Test",
                    state="open",
                    tags=[],
                    url="https://github.com/owner/repo/issues/1",
                    timestamps=AdapterItemTimestamps(created="2026-01-01T00:00:00Z", updated="2026-01-02T00:00:00Z"),
                )
            ],
            metadata=AdapterMetadata(
                producer=AdapterMetadataProducer(name="test", version="1.0.0", build=None),
                run=AdapterMetadataRun(run_id=None, run_attempt=None, actor=None, workflow=None, ref=None, sha=None),
                source=AdapterMetadataSource(systems=["GitHub"], repositories=[], organization=None, enterprise=None),
                original_metadata={},
            ),
            warnings=[CompatibilityWarning(code="TEST_WARNING", message="Test warning message")],
        )
        assert len(result.items) == 1
        assert len(result.warnings) == 1
        assert result.warnings[0].code == "TEST_WARNING"

    def test_create_result_with_empty_warnings(self):
        """Test creating AdapterResult with empty warnings list."""
        result = AdapterResult(
            items=[],
            metadata=AdapterMetadata(
                producer=AdapterMetadataProducer(name="test", version="1.0.0", build=None),
                run=AdapterMetadataRun(run_id=None, run_attempt=None, actor=None, workflow=None, ref=None, sha=None),
                source=AdapterMetadataSource(systems=["GitHub"], repositories=[], organization=None, enterprise=None),
                original_metadata={},
            ),
            warnings=[],
        )
        assert len(result.warnings) == 0

    def test_validation_fails_with_invalid_data(self):
        """Test that validation fails with invalid data."""
        with pytest.raises(ValidationError):
            AdapterResult(items="not a list", metadata={}, warnings=[])  # Should be a list  # Should be AdapterMetadata
