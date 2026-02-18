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
PDF Ready v1.0 Pydantic Models.

Based on SPEC.md section 3.3.
"""

from pydantic import BaseModel, Field, field_validator

from living_doc_datasets_pdf.audit.v1.models import AuditEnvelopeV1


class Timestamps(BaseModel):
    """Timestamps for user story."""

    created: str = Field(..., description="ISO 8601 timestamp")
    updated: str = Field(..., description="ISO 8601 timestamp")

    model_config = {"extra": "forbid", "strict": True}


class Sections(BaseModel):
    """User story sections."""

    description: str | None = Field(None, description="Description (Markdown)")
    business_value: str | None = Field(None, description="Business value (Markdown, optional)")
    preconditions: str | None = Field(None, description="Preconditions (Markdown, optional)")
    acceptance_criteria: str | None = Field(
        None, description="Acceptance criteria (Markdown, optional)"
    )
    user_guide: str | None = Field(None, description="User guide (Markdown, optional)")
    connections: str | None = Field(None, description="Connections (Markdown, optional)")
    last_edited: str | None = Field(None, description="Last edited (Markdown, optional)")

    model_config = {"extra": "forbid", "strict": True}


class UserStory(BaseModel):
    """User story model."""

    id: str = Field(..., description="Canonical stable ID (e.g., 'github:owner/repo#123')")
    title: str = Field(..., description="Title (1-500 chars)")
    state: str = Field(..., description="State (e.g., 'open', 'closed')")
    tags: list[str] = Field(..., description="Tags")
    url: str = Field(..., description="Valid URL")
    timestamps: Timestamps = Field(..., description="Timestamps")
    sections: Sections = Field(..., description="Sections")

    model_config = {"extra": "forbid", "strict": True}

    @field_validator("title")
    @classmethod
    def title_must_be_valid_length(cls, v: str) -> str:
        """Validate that title is 1-500 chars."""
        if not v or len(v) < 1 or len(v) > 500:
            raise ValueError("title must be 1-500 chars")
        return v


class Content(BaseModel):
    """Content section."""

    user_stories: list[UserStory] = Field(..., description="List of user stories")

    model_config = {"extra": "forbid", "strict": True}


class RunContext(BaseModel):
    """Run context (optional)."""

    ci_run_id: str | None = Field(None, description="CI run ID")
    triggered_by: str | None = Field(None, description="Triggered by")
    branch: str | None = Field(None, description="Branch")
    commit_sha: str | None = Field(None, description="Commit SHA")

    model_config = {"extra": "forbid", "strict": True}


class SelectionSummary(BaseModel):
    """Selection summary."""

    total_items: int = Field(..., ge=0, description="Total items (>= 0)")
    included_items: int = Field(..., ge=0, description="Included items (>= 0)")
    excluded_items: int = Field(..., ge=0, description="Excluded items (>= 0)")

    model_config = {"extra": "forbid", "strict": True}


class Meta(BaseModel):
    """Metadata section."""

    document_title: str = Field(..., description="Document title (1-200 chars)")
    document_version: str = Field(..., description="Document version (1-50 chars)")
    generated_at: str = Field(..., description="ISO 8601 UTC timestamp")
    source_set: list[str] = Field(..., description="Source set (non-empty)")
    selection_summary: SelectionSummary = Field(..., description="Selection summary")
    run_context: RunContext | None = Field(None, description="Run context (optional)")
    audit: AuditEnvelopeV1 | None = Field(None, description="Audit envelope (optional)")

    model_config = {"extra": "forbid", "strict": True}

    @field_validator("document_title")
    @classmethod
    def document_title_must_be_valid_length(cls, v: str) -> str:
        """Validate that document_title is 1-200 chars."""
        if not v or len(v) < 1 or len(v) > 200:
            raise ValueError("document_title must be 1-200 chars")
        return v

    @field_validator("document_version")
    @classmethod
    def document_version_must_be_valid_length(cls, v: str) -> str:
        """Validate that document_version is 1-50 chars."""
        if not v or len(v) < 1 or len(v) > 50:
            raise ValueError("document_version must be 1-50 chars")
        return v

    @field_validator("source_set")
    @classmethod
    def source_set_must_be_non_empty(cls, v: list[str]) -> list[str]:
        """Validate that source_set is non-empty."""
        if not v:
            raise ValueError("source_set must be non-empty")
        return v


class PdfReadyV1(BaseModel):
    """PDF Ready v1.0 root model."""

    schema_version: str = Field(..., description="Schema version (must be '1.0')")
    meta: Meta = Field(..., description="Metadata")
    content: Content = Field(..., description="Content")

    model_config = {"extra": "forbid", "strict": True}

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_be_1_0(cls, v: str) -> str:
        """Validate that schema_version is '1.0'."""
        if v != "1.0":
            raise ValueError("schema_version must be '1.0'")
        return v
