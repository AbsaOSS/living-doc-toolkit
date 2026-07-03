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
                "producer": {"name": "AbsaOSS/living-doc-collector-gh", "version": "1.0.0", "build": "test"},
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
            "user_stories": [
                {
                    "id": "github:owner/repo#1",
                    "title": "Test Issue",
                    "state": "open",
                    "tags": ["test"],
                    "url": "https://github.com/owner/repo/issues/1",
                    "timestamps": {
                        "created": "2026-01-01T00:00:00Z",
                        "updated": "2026-01-02T00:00:00Z",
                    },
                    "description": "Test description",
                }
            ],
        }

    def test_parse_v1_0_0_fixture(self, fixture_v1_0_0):
        """Test parsing with v1.0.0 fixture."""
        result = parse(fixture_v1_0_0)

        assert len(result.user_stories) == 12

        assert result.metadata.producer.name == "AbsaOSS/living-doc-collector-gh"
        assert result.metadata.producer.version == "1.0.0"
        assert result.metadata.producer.build == "sha-abc123"

        assert len(result.warnings) == 0

        assert "producer" in result.metadata.original_metadata
        assert result.metadata.original_metadata["producer"]["version"] == "1.0.0"

    def test_parse_v1_2_0_fixture(self, fixture_v1_2_0):
        """Test parsing with v1.2.0 fixture."""
        result = parse(fixture_v1_2_0)

        assert len(result.user_stories) == 12

        assert result.metadata.producer.name == "AbsaOSS/living-doc-collector-gh"
        assert result.metadata.producer.version == "1.2.0"
        assert result.metadata.producer.build == "sha-xyz789"

        assert len(result.warnings) == 0

    def test_adapter_item_id_format(self, fixture_v1_0_0):
        """Test that AdapterItem ID has correct format."""
        result = parse(fixture_v1_0_0)

        assert result.user_stories[0].id == "github:AbsaOSS/example-project#1"
        assert result.user_stories[1].id == "github:AbsaOSS/example-project#2"

    def test_adapter_item_fields_mapped(self, fixture_v1_0_0):
        """Test that AdapterItem fields are correctly mapped."""
        result = parse(fixture_v1_0_0)

        first_item = result.user_stories[0]
        assert first_item.title == "User Authentication with OAuth2"
        assert first_item.state == "open"
        assert "documentation" in first_item.tags
        assert "priority:high" in first_item.tags
        assert first_item.url == "https://github.com/AbsaOSS/example-project/issues/1"
        assert first_item.timestamps.created == "2026-01-10T08:00:00Z"
        assert first_item.timestamps.updated == "2026-01-20T14:30:00Z"
        assert first_item.description is not None
        assert "OAuth2" in first_item.description

    def test_adapter_item_structured_fields(self, fixture_v1_0_0):
        """Test that structured fields are parsed into the item."""
        result = parse(fixture_v1_0_0)

        first_item = result.user_stories[0]
        assert first_item.business_value == ["Business value for issue 1."]
        assert first_item.preconditions == ["User is logged in."]
        assert first_item.acceptance_criteria is not None
        ac = first_item.acceptance_criteria[0]
        assert ac.id == "GH-1-01"
        assert ac.state == "Active"
        assert ac.version == "v1.0.0"
        assert ac.description == "First criterion for issue 1."

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
        assert "producer" in original
        assert "run" in original
        assert "source" in original
        assert original["producer"]["name"] == "AbsaOSS/living-doc-collector-gh"

    def test_parse_minimal_payload(self, minimal_payload):
        """Test parsing with minimal payload."""
        result = parse(minimal_payload)

        assert len(result.user_stories) == 1
        assert result.user_stories[0].id == "github:owner/repo#1"
        assert result.user_stories[0].title == "Test Issue"

    def test_parse_with_missing_labels(self, minimal_payload):
        """Test parsing when tags are missing from item."""
        minimal_payload["user_stories"][0].pop("tags")
        result = parse(minimal_payload)

        assert len(result.user_stories) == 1
        assert result.user_stories[0].tags == []

    def test_parse_with_missing_description(self, minimal_payload):
        """Test parsing when description is missing from item."""
        minimal_payload["user_stories"][0].pop("description")
        result = parse(minimal_payload)

        assert len(result.user_stories) == 1
        assert result.user_stories[0].description is None

    def test_parse_with_no_repositories(self, minimal_payload):
        """Test that empty repositories list raises AdapterError (required by schema)."""
        minimal_payload["metadata"]["source"]["repositories"] = []

        with pytest.raises(AdapterError) as exc_info:
            parse(minimal_payload)
        assert "repositories cannot be empty" in str(exc_info.value)

    def test_parse_with_incompatible_version(self, minimal_payload):
        """Test parsing with incompatible version generates warnings."""
        minimal_payload["metadata"]["producer"]["version"] = "2.0.0"
        result = parse(minimal_payload)

        assert len(result.warnings) == 1
        assert result.warnings[0].code == "VERSION_MISMATCH"
        assert "2.0.0" in result.warnings[0].message

    def test_parse_with_closed_issue(self, fixture_v1_0_0):
        """Test parsing includes closed issues."""
        result = parse(fixture_v1_0_0)

        closed_items = [item for item in result.user_stories if item.state == "closed"]
        assert len(closed_items) > 0
        assert closed_items[0].state == "closed"

    def test_parse_missing_item_field_raises_error(self, minimal_payload):
        """Test that missing required item field raises AdapterError."""
        del minimal_payload["user_stories"][0]["title"]

        with pytest.raises(AdapterError) as exc_info:
            parse(minimal_payload)
        assert "missing required field" in str(exc_info.value)

    def test_parse_missing_metadata_raises_error(self):
        """Test that missing metadata raises AdapterError."""
        payload = {"user_stories": []}

        with pytest.raises(AdapterError):
            parse(payload)

    def test_parse_missing_user_stories_raises_error(self):
        """Test that a missing user_stories key raises AdapterError."""
        payload = {
            "metadata": {
                "producer": {"name": "AbsaOSS/living-doc-collector-gh", "version": "1.0.0", "build": None},
                "run": {"run_id": None, "run_attempt": None, "actor": None, "workflow": None, "ref": None, "sha": None},
                "source": {
                    "systems": ["GitHub"],
                    "repositories": ["owner/repo"],
                    "organization": "owner",
                    "enterprise": None,
                },
            }
        }

        with pytest.raises(AdapterError) as exc_info:
            parse(payload)
        assert "user_stories" in str(exc_info.value)

    def test_parse_empty_user_stories_list(self, minimal_payload):
        """Test parsing with empty user_stories list."""
        minimal_payload["user_stories"] = []
        result = parse(minimal_payload)

        assert len(result.user_stories) == 0
        assert len(result.warnings) == 0

    def test_parse_null_acceptance_criteria(self, minimal_payload):
        """Test parsing an item whose acceptance_criteria is null."""
        minimal_payload["user_stories"][0]["acceptance_criteria"] = None
        result = parse(minimal_payload)

        assert result.user_stories[0].acceptance_criteria is None


class TestParseAcceptanceCriteria:
    """Tests for acceptance-criteria parsing behavior."""

    def _payload(self, item):
        return {
            "metadata": {
                "producer": {"name": "AbsaOSS/living-doc-collector-gh", "version": "0.1.1", "build": None},
                "run": {"run_id": None, "run_attempt": None, "actor": None, "workflow": None, "ref": None, "sha": None},
                "source": {
                    "systems": ["GitHub"],
                    "repositories": ["owner/repo"],
                    "organization": "owner",
                    "enterprise": None,
                },
                "original_metadata": {},
            },
            "user_stories": [item],
            "warnings": [],
        }

    def test_structured_fields_populated(self):
        """Test that parse populates the structured fields from the item."""
        item = {
            "id": "owner/repo/1",
            "title": "View domain",
            "state": "open",
            "tags": ["DocumentedUserStory"],
            "url": "https://github.com/owner/repo/issues/1",
            "timestamps": {"created": "2025-12-17T11:31:16+00:00", "updated": "2026-04-09T07:10:01+00:00"},
            "description": "As a user, I want to view the details of a selected domain.",
            "business_value": ["Streamlines domain details visibility."],
            "preconditions": ["The user has logged in."],
            "acceptance_criteria": [
                {"id": "GH-28-01", "state": "Active", "version": "v1.5.0", "description": "User can access details."},
            ],
        }

        result = parse(self._payload(item))

        assert len(result.user_stories) == 1
        story = result.user_stories[0]
        assert story.description == "As a user, I want to view the details of a selected domain."
        assert story.business_value == ["Streamlines domain details visibility."]
        assert story.preconditions == ["The user has logged in."]
        assert story.acceptance_criteria is not None
        assert story.acceptance_criteria[0].id == "GH-28-01"
        assert story.acceptance_criteria[0].state == "Active"
        assert story.acceptance_criteria[0].version == "v1.5.0"
        assert story.acceptance_criteria[0].description == "User can access details."

    def test_null_structured_fields(self):
        """Test that an item with null structured fields parses cleanly."""
        item = {
            "id": "owner/repo/15",
            "title": "Add data feeds",
            "state": "closed",
            "tags": ["DocumentedUserStory"],
            "url": "https://github.com/owner/repo/issues/15",
            "timestamps": {"created": "2025-11-21T10:27:16+00:00", "updated": "2026-03-30T08:41:28+00:00"},
            "description": None,
            "business_value": None,
            "preconditions": None,
            "acceptance_criteria": None,
        }

        result = parse(self._payload(item))

        story = result.user_stories[0]
        assert story.description is None
        assert story.business_value is None
        assert story.preconditions is None
        assert story.acceptance_criteria is None
