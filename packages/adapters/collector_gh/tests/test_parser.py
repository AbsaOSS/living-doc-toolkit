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
            "items": [
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
        assert "producer" in result.metadata.original_metadata
        assert result.metadata.original_metadata["producer"]["version"] == "1.0.0"

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
        assert "producer" in original
        assert "run" in original
        assert "source" in original
        assert original["producer"]["name"] == "AbsaOSS/living-doc-collector-gh"

    def test_parse_minimal_payload(self, minimal_payload):
        """Test parsing with minimal payload."""
        result = parse(minimal_payload)

        assert len(result.items) == 1
        assert result.items[0].id == "github:owner/repo#1"
        assert result.items[0].title == "Test Issue"

    def test_parse_with_missing_labels(self, minimal_payload):
        """Test parsing when tags are missing from item."""
        minimal_payload["items"][0].pop("tags")
        result = parse(minimal_payload)

        assert len(result.items) == 1
        assert result.items[0].tags == []

    def test_parse_with_missing_body(self, minimal_payload):
        """Test parsing when body is missing from item."""
        minimal_payload["items"][0].pop("body")
        result = parse(minimal_payload)

        assert len(result.items) == 1
        assert result.items[0].body is None

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

        # Find a closed issue
        closed_items = [item for item in result.items if item.state == "closed"]
        assert len(closed_items) > 0

        closed_item = closed_items[0]
        assert closed_item.state == "closed"

    def test_parse_missing_item_field_raises_error(self, minimal_payload):
        """Test that missing required item field raises AdapterError."""
        del minimal_payload["items"][0]["title"]

        with pytest.raises(AdapterError) as exc_info:
            parse(minimal_payload)
        assert "missing required field" in str(exc_info.value)

    def test_parse_missing_metadata_raises_error(self):
        """Test that missing metadata raises AdapterError."""
        payload = {"items": []}

        with pytest.raises(AdapterError):
            parse(payload)

    def test_parse_empty_items_list(self, minimal_payload):
        """Test parsing with empty items list."""
        minimal_payload["items"] = []
        result = parse(minimal_payload)

        assert len(result.items) == 0
        assert len(result.warnings) == 0


class TestBuildBodyFromStructured:
    """Tests for the _build_body_from_structured helper."""

    def test_all_structured_fields_present(self):
        """Test markdown body is built only from description when all structured fields are present."""
        from living_doc_adapter_collector_gh.parser import _build_body_from_structured

        raw_item = {
            "description": "As a user, I want to view domain details.",
            "business_value": ["Streamlines domain visibility.", "Improves clarity."],
            "preconditions": ["User is logged in.", "At least one domain exists."],
            "acceptance_criteria": [
                {"id": "GH-28-01", "state": "Active", "version": "v1.5.0", "description": "User can access details."},
                {"id": "GH-28-02", "state": "Active", "version": "v1.5.0", "description": "Domain card is visible."},
            ],
        }

        body = _build_body_from_structured(raw_item)

        # body now only contains description
        assert body == "## Description\nAs a user, I want to view domain details."
        # bv/pc/ac are NOT in the body; they flow through structured fields
        assert "Business Value" not in body
        assert "Preconditions" not in body
        assert "Acceptance Criteria" not in body

    def test_only_description_present(self):
        """Test body built with description only."""
        from living_doc_adapter_collector_gh.parser import _build_body_from_structured

        body = _build_body_from_structured({"description": "Simple description."})

        assert body == "## Description\nSimple description."

    def test_no_structured_fields_returns_none(self):
        """Test that None is returned when no structured fields are present."""
        from living_doc_adapter_collector_gh.parser import _build_body_from_structured

        assert _build_body_from_structured({}) is None
        assert _build_body_from_structured({"title": "No structured content"}) is None

    def test_acceptance_criteria_without_meta(self):
        """Test that structured AC entries without state/version still parse cleanly."""
        from living_doc_adapter_collector_gh.parser import parse

        payload = {
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
            "items": [
                {
                    "id": "owner/repo/1",
                    "title": "Test",
                    "state": "open",
                    "tags": [],
                    "url": "https://github.com/owner/repo/issues/1",
                    "timestamps": {"created": "2025-01-01T00:00:00+00:00", "updated": "2025-01-01T00:00:00+00:00"},
                    "acceptance_criteria": [
                        {"id": None, "state": None, "version": None, "description": "Something happens."}
                    ],
                }
            ],
            "warnings": [],
        }
        result = parse(payload)
        ac = result.items[0].structured_acceptance_criteria
        assert ac is not None
        assert ac[0].description == "Something happens."
        assert ac[0].id is None

    def test_structured_fields_used_when_body_absent(self):
        """Test that parse populates structured fields from item when body is missing."""
        payload = {
            "metadata": {
                "producer": {"name": "AbsaOSS/living-doc-collector-gh", "version": "0.1.1", "build": None},
                "run": {
                    "run_id": None,
                    "run_attempt": None,
                    "actor": None,
                    "workflow": None,
                    "ref": None,
                    "sha": None,
                },
                "source": {
                    "systems": ["GitHub"],
                    "repositories": ["owner/repo"],
                    "organization": "owner",
                    "enterprise": None,
                },
                "original_metadata": {},
            },
            "items": [
                {
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
                        {
                            "id": "GH-28-01",
                            "state": "Active",
                            "version": "v1.5.0",
                            "description": "User can access details.",
                        },
                    ],
                }
            ],
            "warnings": [],
        }

        result = parse(payload)

        assert len(result.items) == 1
        item = result.items[0]
        # body carries only the description
        assert item.body == "## Description\nAs a user, I want to view the details of a selected domain."
        # structured fields are populated directly
        assert item.structured_business_value == ["Streamlines domain details visibility."]
        assert item.structured_preconditions == ["The user has logged in."]
        assert item.structured_acceptance_criteria is not None
        assert item.structured_acceptance_criteria[0].id == "GH-28-01"
        assert item.structured_acceptance_criteria[0].state == "Active"
        assert item.structured_acceptance_criteria[0].version == "v1.5.0"
        assert item.structured_acceptance_criteria[0].description == "User can access details."

    def test_explicit_body_not_overridden_by_structured_fields(self):
        """Test that an explicit body field takes precedence over structured fields."""
        payload = {
            "metadata": {
                "producer": {"name": "AbsaOSS/living-doc-collector-gh", "version": "0.1.1", "build": None},
                "run": {
                    "run_id": None,
                    "run_attempt": None,
                    "actor": None,
                    "workflow": None,
                    "ref": None,
                    "sha": None,
                },
                "source": {
                    "systems": ["GitHub"],
                    "repositories": ["owner/repo"],
                    "organization": "owner",
                    "enterprise": None,
                },
                "original_metadata": {},
            },
            "items": [
                {
                    "id": "owner/repo/2",
                    "title": "Edit domain",
                    "state": "open",
                    "tags": [],
                    "url": "https://github.com/owner/repo/issues/2",
                    "timestamps": {"created": "2025-12-17T11:31:16+00:00", "updated": "2026-04-09T07:10:01+00:00"},
                    "body": "## Description\nExplicit markdown body.",
                    "description": "Should be ignored.",
                }
            ],
            "warnings": [],
        }

        result = parse(payload)

        assert result.items[0].body == "## Description\nExplicit markdown body."
