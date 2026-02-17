# Copyright 2026 AbsaOSS
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Unit tests for PDF Ready v1 models.
"""

import json

import pytest
from pydantic import ValidationError

from living_doc_datasets_pdf.audit.v1.models import AuditEnvelopeV1
from living_doc_datasets_pdf.pdf_ready.v1.models import (
    Content,
    Meta,
    PdfReadyV1,
    RunContext,
    Sections,
    SelectionSummary,
    Timestamps,
    UserStory,
)
from living_doc_datasets_pdf.pdf_ready.v1.serializer import from_json, to_json


def test_valid_pdf_ready_from_spec():
    """Test valid PDF Ready model with example from SPEC.md 3.3.4."""
    data = {
        "schema_version": "1.0",
        "meta": {
            "document_title": "Product Requirements - Release 2.1",
            "document_version": "2.1.0",
            "generated_at": "2026-01-23T12:00:00Z",
            "source_set": ["github:AbsaOSS/project"],
            "selection_summary": {"total_items": 15, "included_items": 12, "excluded_items": 3},
            "audit": {
                "schema_version": "1.0",
                "producer": {
                    "name": "AbsaOSS/living-doc-collector-gh",
                    "version": "1.2.0",
                    "build": "abc123",
                },
                "run": {
                    "run_id": "123456",
                    "run_attempt": "1",
                    "actor": "user@example.com",
                    "workflow": "collect-docs",
                    "ref": "refs/heads/main",
                    "sha": "abc123def456",
                },
                "source": {
                    "systems": ["GitHub"],
                    "repositories": ["AbsaOSS/project"],
                    "organization": "AbsaOSS",
                    "enterprise": None,
                },
                "trace": [
                    {
                        "step": "collection",
                        "tool": "living-doc-collector-gh",
                        "tool_version": "1.2.0",
                        "started_at": "2026-01-23T11:50:00Z",
                        "finished_at": "2026-01-23T11:55:00Z",
                        "warnings": [],
                    },
                    {
                        "step": "normalization",
                        "tool": "living-doc-toolkit",
                        "tool_version": "0.1.0",
                        "started_at": "2026-01-23T12:00:00Z",
                        "finished_at": "2026-01-23T12:00:05Z",
                        "warnings": [],
                    },
                ],
                "extensions": {"collector-gh": {"original_metadata": {}}},
            },
        },
        "content": {
            "user_stories": [
                {
                    "id": "github:AbsaOSS/project#42",
                    "title": "User login with SSO",
                    "state": "open",
                    "tags": ["authentication", "priority:high"],
                    "url": "https://github.com/AbsaOSS/project/issues/42",
                    "timestamps": {"created": "2026-01-10T08:00:00Z", "updated": "2026-01-20T14:30:00Z"},
                    "sections": {
                        "description": "As a user, I want to log in using SSO...",
                        "business_value": "Reduces friction for enterprise users",
                        "preconditions": "SSO provider configured",
                        "acceptance_criteria": "- User can click SSO button\n- Redirect to provider\n- Return with session",
                        "user_guide": None,
                        "connections": "Related to #41, #43",
                        "last_edited": "Updated by alice@example.com on 2026-01-20",
                    },
                }
            ]
        },
    }

    pdf_ready = PdfReadyV1.model_validate(data)

    assert pdf_ready.schema_version == "1.0"
    assert pdf_ready.meta.document_title == "Product Requirements - Release 2.1"
    assert pdf_ready.meta.document_version == "2.1.0"
    assert pdf_ready.meta.source_set == ["github:AbsaOSS/project"]
    assert pdf_ready.meta.selection_summary.total_items == 15
    assert pdf_ready.meta.selection_summary.included_items == 12
    assert pdf_ready.meta.selection_summary.excluded_items == 3
    assert pdf_ready.meta.audit is not None
    assert pdf_ready.meta.audit.schema_version == "1.0"
    assert len(pdf_ready.content.user_stories) == 1
    assert pdf_ready.content.user_stories[0].id == "github:AbsaOSS/project#42"
    assert pdf_ready.content.user_stories[0].title == "User login with SSO"


def test_invalid_schema_version():
    """Test that schema_version must be '1.0'."""
    data = {
        "schema_version": "2.0",
        "meta": {
            "document_title": "Test",
            "document_version": "1.0",
            "generated_at": "2026-01-23T12:00:00Z",
            "source_set": ["test"],
            "selection_summary": {"total_items": 0, "included_items": 0, "excluded_items": 0},
        },
        "content": {"user_stories": []},
    }

    with pytest.raises(ValidationError) as exc_info:
        PdfReadyV1.model_validate(data)

    assert "schema_version must be '1.0'" in str(exc_info.value)


def test_invalid_document_title_too_long():
    """Test that document_title must be 1-200 chars."""
    data = {
        "schema_version": "1.0",
        "meta": {
            "document_title": "x" * 201,
            "document_version": "1.0",
            "generated_at": "2026-01-23T12:00:00Z",
            "source_set": ["test"],
            "selection_summary": {"total_items": 0, "included_items": 0, "excluded_items": 0},
        },
        "content": {"user_stories": []},
    }

    with pytest.raises(ValidationError) as exc_info:
        PdfReadyV1.model_validate(data)

    assert "document_title must be 1-200 chars" in str(exc_info.value)


def test_invalid_document_title_empty():
    """Test that document_title cannot be empty."""
    data = {
        "schema_version": "1.0",
        "meta": {
            "document_title": "",
            "document_version": "1.0",
            "generated_at": "2026-01-23T12:00:00Z",
            "source_set": ["test"],
            "selection_summary": {"total_items": 0, "included_items": 0, "excluded_items": 0},
        },
        "content": {"user_stories": []},
    }

    with pytest.raises(ValidationError) as exc_info:
        PdfReadyV1.model_validate(data)

    assert "document_title must be 1-200 chars" in str(exc_info.value)


def test_invalid_document_version_too_long():
    """Test that document_version must be 1-50 chars."""
    data = {
        "schema_version": "1.0",
        "meta": {
            "document_title": "Test",
            "document_version": "x" * 51,
            "generated_at": "2026-01-23T12:00:00Z",
            "source_set": ["test"],
            "selection_summary": {"total_items": 0, "included_items": 0, "excluded_items": 0},
        },
        "content": {"user_stories": []},
    }

    with pytest.raises(ValidationError) as exc_info:
        PdfReadyV1.model_validate(data)

    assert "document_version must be 1-50 chars" in str(exc_info.value)


def test_invalid_source_set_empty():
    """Test that source_set must be non-empty."""
    data = {
        "schema_version": "1.0",
        "meta": {
            "document_title": "Test",
            "document_version": "1.0",
            "generated_at": "2026-01-23T12:00:00Z",
            "source_set": [],
            "selection_summary": {"total_items": 0, "included_items": 0, "excluded_items": 0},
        },
        "content": {"user_stories": []},
    }

    with pytest.raises(ValidationError) as exc_info:
        PdfReadyV1.model_validate(data)

    assert "source_set must be non-empty" in str(exc_info.value)


def test_invalid_title_too_long():
    """Test that user story title must be 1-500 chars."""
    data = {
        "schema_version": "1.0",
        "meta": {
            "document_title": "Test",
            "document_version": "1.0",
            "generated_at": "2026-01-23T12:00:00Z",
            "source_set": ["test"],
            "selection_summary": {"total_items": 1, "included_items": 1, "excluded_items": 0},
        },
        "content": {
            "user_stories": [
                {
                    "id": "test:1",
                    "title": "x" * 501,
                    "state": "open",
                    "tags": [],
                    "url": "https://example.com",
                    "timestamps": {"created": "2026-01-01T00:00:00Z", "updated": "2026-01-01T00:00:00Z"},
                    "sections": {"description": None},
                }
            ]
        },
    }

    with pytest.raises(ValidationError) as exc_info:
        PdfReadyV1.model_validate(data)

    assert "title must be 1-500 chars" in str(exc_info.value)


def test_missing_required_fields():
    """Test that missing required fields raise ValidationError."""
    data = {"schema_version": "1.0"}

    with pytest.raises(ValidationError):
        PdfReadyV1.model_validate(data)


def test_extra_fields_forbidden():
    """Test that extra fields are forbidden."""
    data = {
        "schema_version": "1.0",
        "meta": {
            "document_title": "Test",
            "document_version": "1.0",
            "generated_at": "2026-01-23T12:00:00Z",
            "source_set": ["test"],
            "selection_summary": {"total_items": 0, "included_items": 0, "excluded_items": 0},
        },
        "content": {"user_stories": []},
        "extra_field": "not allowed",
    }

    with pytest.raises(ValidationError) as exc_info:
        PdfReadyV1.model_validate(data)

    assert "Extra inputs are not permitted" in str(exc_info.value)


def test_selection_summary_validation():
    """Test SelectionSummary validation."""
    summary = SelectionSummary(total_items=10, included_items=7, excluded_items=3)

    assert summary.total_items == 10
    assert summary.included_items == 7
    assert summary.excluded_items == 3


def test_selection_summary_negative_values():
    """Test that SelectionSummary does not allow negative values."""
    with pytest.raises(ValidationError):
        SelectionSummary(total_items=-1, included_items=0, excluded_items=0)


def test_run_context_optional():
    """Test RunContext is optional."""
    data = {
        "schema_version": "1.0",
        "meta": {
            "document_title": "Test",
            "document_version": "1.0",
            "generated_at": "2026-01-23T12:00:00Z",
            "source_set": ["test"],
            "selection_summary": {"total_items": 0, "included_items": 0, "excluded_items": 0},
            "run_context": None,
        },
        "content": {"user_stories": []},
    }

    pdf_ready = PdfReadyV1.model_validate(data)
    assert pdf_ready.meta.run_context is None


def test_run_context_with_data():
    """Test RunContext with data."""
    context = RunContext(ci_run_id="123", triggered_by="user@example.com", branch="main", commit_sha="abc123")

    assert context.ci_run_id == "123"
    assert context.triggered_by == "user@example.com"
    assert context.branch == "main"
    assert context.commit_sha == "abc123"


def test_sections_all_optional():
    """Test that all Sections fields are optional."""
    sections = Sections(
        description=None,
        business_value=None,
        preconditions=None,
        acceptance_criteria=None,
        user_guide=None,
        connections=None,
        last_edited=None,
    )

    assert sections.description is None
    assert sections.business_value is None
    assert sections.preconditions is None
    assert sections.acceptance_criteria is None
    assert sections.user_guide is None
    assert sections.connections is None
    assert sections.last_edited is None


def test_serialization_round_trip():
    """Test serialization and deserialization round-trip."""
    data = {
        "schema_version": "1.0",
        "meta": {
            "document_title": "Test",
            "document_version": "1.0",
            "generated_at": "2026-01-23T12:00:00Z",
            "source_set": ["test"],
            "selection_summary": {"total_items": 0, "included_items": 0, "excluded_items": 0},
            "run_context": None,
            "audit": None,
        },
        "content": {"user_stories": []},
    }

    pdf_ready1 = PdfReadyV1.model_validate(data)
    json_str = to_json(pdf_ready1)
    pdf_ready2 = from_json(json_str)

    assert pdf_ready1.model_dump() == pdf_ready2.model_dump()


def test_deterministic_serialization():
    """Test that serialization produces deterministic output."""
    pdf_ready = PdfReadyV1(
        schema_version="1.0",
        meta=Meta(
            document_title="Test",
            document_version="1.0",
            generated_at="2026-01-23T12:00:00Z",
            source_set=["test"],
            selection_summary=SelectionSummary(total_items=0, included_items=0, excluded_items=0),
            run_context=None,
            audit=None,
        ),
        content=Content(user_stories=[]),
    )

    json1 = to_json(pdf_ready)
    json2 = to_json(pdf_ready)

    assert json1 == json2


def test_complete_user_story():
    """Test complete UserStory with all sections."""
    story = UserStory(
        id="github:owner/repo#1",
        title="Test Story",
        state="open",
        tags=["tag1", "tag2"],
        url="https://github.com/owner/repo/issues/1",
        timestamps=Timestamps(created="2026-01-01T00:00:00Z", updated="2026-01-02T00:00:00Z"),
        sections=Sections(
            description="Test description",
            business_value="Test value",
            preconditions="Test preconditions",
            acceptance_criteria="Test criteria",
            user_guide="Test guide",
            connections="Test connections",
            last_edited="Test edit",
        ),
    )

    assert story.id == "github:owner/repo#1"
    assert story.title == "Test Story"
    assert len(story.tags) == 2
    assert story.sections.description == "Test description"
    assert story.sections.business_value == "Test value"
