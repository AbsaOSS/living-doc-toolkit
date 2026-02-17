# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for the parser module."""

import json
from pathlib import Path

import pytest
from living_doc_core.errors import AdapterError

from living_doc_adapter_collector_gh.parser import parse


class TestParser:
    """Tests for the parse function."""

    @pytest.fixture
    def fixture_v1_0_0(self):
        """Load the v1.0.0 fixture file."""
        fixture_path = Path(__file__).parent / "fixtures" / "collector_v1.0.0" / "input" / "doc-issues.json"
        with open(fixture_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @pytest.fixture
    def fixture_v1_2_0(self):
        """Load the v1.2.0 fixture file."""
        fixture_path = Path(__file__).parent / "fixtures" / "collector_v1.2.0" / "input" / "doc-issues.json"
        with open(fixture_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @pytest.fixture
    def minimal_payload(self):
        """Create a minimal valid payload."""
        return {
            "metadata": {
                "generator": {"name": "AbsaOSS/living-doc-collector-gh", "version": "1.0.0", "build": "test"},
                "run": {
                    "run_id": "123",
                    "run_attempt": "1",
                    "actor": "test@example.com",
                    "workflow": "test",
                    "ref": "refs/heads/main",
                    "sha": "abc123",
                },
                "source": {
                    "systems": ["GitHub"],
                    "repositories": ["owner/repo"],
                    "organization": "owner",
                    "enterprise": None,
                },
            },
            "issues": [
                {
                    "number": 1,
                    "title": "Test Issue",
                    "state": "open",
                    "labels": ["test"],
                    "html_url": "https://github.com/owner/repo/issues/1",
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-02T00:00:00Z",
                    "body": "Test body",
                }
            ],
        }

    def test_parse_v1_0_0_fixture(self, fixture_v1_0_0):
        """Test parsing with v1.0.0 fixture."""
        result = parse(fixture_v1_0_0)

        # Check that we have the correct number of items
        assert len(result.items) == 12

        # Check metadata
        assert result.metadata.producer.name == "AbsaOSS/living-doc-collector-gh"
        assert result.metadata.producer.version == "1.0.0"
        assert result.metadata.producer.build == "sha-abc123"

        # Check no warnings for version 1.0.0
        assert len(result.warnings) == 0

        # Check original metadata is preserved
        assert "generator" in result.metadata.original_metadata
        assert result.metadata.original_metadata["generator"]["version"] == "1.0.0"

    def test_parse_v1_2_0_fixture(self, fixture_v1_2_0):
        """Test parsing with v1.2.0 fixture."""
        result = parse(fixture_v1_2_0)

        # Check that we have the correct number of items
        assert len(result.items) == 12

        # Check metadata
        assert result.metadata.producer.name == "AbsaOSS/living-doc-collector-gh"
        assert result.metadata.producer.version == "1.2.0"
        assert result.metadata.producer.build == "sha-xyz789"

        # Check no warnings for version 1.2.0
        assert len(result.warnings) == 0

    def test_adapter_item_id_format(self, fixture_v1_0_0):
        """Test that AdapterItem ID has correct format."""
        result = parse(fixture_v1_0_0)

        # Check first item
        first_item = result.items[0]
        assert first_item.id == "github:AbsaOSS/example-project#1"

        # Check another item
        second_item = result.items[1]
        assert second_item.id == "github:AbsaOSS/example-project#2"

    def test_adapter_item_fields_mapped(self, fixture_v1_0_0):
        """Test that AdapterItem fields are correctly mapped."""
        result = parse(fixture_v1_0_0)

        first_item = result.items[0]
        assert first_item.title == "User Authentication with OAuth2"
        assert first_item.state == "open"
        assert "documentation" in first_item.tags
        assert "priority:high" in first_item.tags
        assert first_item.url == "https://github.com/AbsaOSS/example-project/issues/1"
        assert first_item.timestamps.created == "2026-01-10T08:00:00Z"
        assert first_item.timestamps.updated == "2026-01-20T14:30:00Z"
        assert first_item.body is not None
        assert "OAuth2" in first_item.body

    def test_metadata_producer_mapping(self, fixture_v1_0_0):
        """Test that producer metadata is correctly mapped."""
        result = parse(fixture_v1_0_0)

        assert result.metadata.producer.name == "AbsaOSS/living-doc-collector-gh"
        assert result.metadata.producer.version == "1.0.0"
        assert result.metadata.producer.build == "sha-abc123"

    def test_metadata_run_mapping(self, fixture_v1_0_0):
        """Test that run metadata is correctly mapped."""
        result = parse(fixture_v1_0_0)

        assert result.metadata.run.run_id == "123456789"
        assert result.metadata.run.run_attempt == "1"
        assert result.metadata.run.actor == "john.doe@example.com"
        assert result.metadata.run.workflow == "collect-documentation"
        assert result.metadata.run.ref == "refs/heads/main"
        assert result.metadata.run.sha == "abc123def456789"

    def test_metadata_source_mapping(self, fixture_v1_0_0):
        """Test that source metadata is correctly mapped."""
        result = parse(fixture_v1_0_0)

        assert result.metadata.source.systems == ["GitHub"]
        assert result.metadata.source.repositories == ["AbsaOSS/example-project"]
        assert result.metadata.source.organization == "AbsaOSS"
        assert result.metadata.source.enterprise is None

    def test_original_metadata_preserved(self, fixture_v1_0_0):
        """Test that original metadata is preserved."""
        result = parse(fixture_v1_0_0)

        original = result.metadata.original_metadata
        assert "generator" in original
        assert "run" in original
        assert "source" in original
        assert original["generator"]["name"] == "AbsaOSS/living-doc-collector-gh"

    def test_parse_minimal_payload(self, minimal_payload):
        """Test parsing with minimal payload."""
        result = parse(minimal_payload)

        assert len(result.items) == 1
        assert result.items[0].id == "github:owner/repo#1"
        assert result.items[0].title == "Test Issue"

    def test_parse_with_missing_labels(self, minimal_payload):
        """Test parsing when labels are missing from issue."""
        minimal_payload["issues"][0].pop("labels")
        result = parse(minimal_payload)

        assert len(result.items) == 1
        assert result.items[0].tags == []

    def test_parse_with_missing_body(self, minimal_payload):
        """Test parsing when body is missing from issue."""
        minimal_payload["issues"][0].pop("body")
        result = parse(minimal_payload)

        assert len(result.items) == 1
        assert result.items[0].body is None

    def test_parse_with_no_repositories(self, minimal_payload):
        """Test parsing when repositories list is empty."""
        minimal_payload["metadata"]["source"]["repositories"] = []
        result = parse(minimal_payload)

        # Should use fallback repo name
        assert result.items[0].id == "github:unknown/repo#1"

    def test_parse_with_incompatible_version(self, minimal_payload):
        """Test parsing with incompatible version generates warnings."""
        minimal_payload["metadata"]["generator"]["version"] = "2.0.0"
        result = parse(minimal_payload)

        assert len(result.warnings) == 1
        assert result.warnings[0].code == "VERSION_MISMATCH"
        assert "2.0.0" in result.warnings[0].message

    def test_parse_with_closed_issue(self, fixture_v1_0_0):
        """Test parsing includes closed issues."""
        result = parse(fixture_v1_0_0)

        # Find a closed issue
        closed_items = [item for item in result.items if item.state == "closed"]
        assert len(closed_items) > 0

        closed_item = closed_items[0]
        assert closed_item.state == "closed"

    def test_parse_missing_issue_field_raises_error(self, minimal_payload):
        """Test that missing required issue field raises AdapterError."""
        # Remove required field from issue
        del minimal_payload["issues"][0]["title"]

        with pytest.raises(AdapterError) as exc_info:
            parse(minimal_payload)
        assert "Failed to parse issue" in str(exc_info.value)

    def test_parse_missing_metadata_raises_error(self):
        """Test that missing metadata raises AdapterError."""
        payload = {"issues": []}

        with pytest.raises(AdapterError):
            parse(payload)

    def test_parse_empty_issues_list(self, minimal_payload):
        """Test parsing with empty issues list."""
        minimal_payload["issues"] = []
        result = parse(minimal_payload)

        assert len(result.items) == 0
        assert len(result.warnings) == 0
