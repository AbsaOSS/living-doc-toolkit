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
Audit Envelope v1.0 Pydantic Models.

Based on SPEC.md section 3.4.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class AuditWarning(BaseModel):
    """Warning in trace step."""

    code: str = Field(..., description="Warning code (e.g., 'VERSION_MISMATCH')")
    message: str = Field(..., description="Human-readable message")
    context: str | None = Field(None, description="Optional context (e.g., field path)")

    model_config = {"extra": "forbid", "strict": True}


class TraceStep(BaseModel):
    """Trace step in audit trail."""

    step: str = Field(..., description="Step name (e.g., 'collection', 'normalization')")
    tool: str = Field(..., description="Tool name")
    tool_version: str = Field(..., description="Tool version (semver)")
    started_at: str | None = Field(None, description="ISO 8601 timestamp")
    finished_at: str | None = Field(None, description="ISO 8601 timestamp")
    warnings: list[AuditWarning] = Field(default_factory=list, description="List of warnings")

    model_config = {"extra": "forbid", "strict": True}


class Source(BaseModel):
    """Source metadata."""

    systems: list[str] = Field(..., description="Source systems (required, non-empty)")
    repositories: list[str] = Field(default_factory=list, description="Source repositories")
    organization: str | None = Field(None, description="Organization name")
    enterprise: str | None = Field(None, description="Enterprise name")

    model_config = {"extra": "forbid", "strict": True}

    @field_validator("systems")
    @classmethod
    def systems_must_be_non_empty(cls, v: list[str]) -> list[str]:
        """Validate that systems is non-empty."""
        if not v:
            raise ValueError("systems must be non-empty")
        return v


class Run(BaseModel):
    """Run metadata."""

    run_id: str | None = Field(None, description="Run ID")
    run_attempt: str | None = Field(None, description="Run attempt")
    actor: str | None = Field(None, description="Actor")
    workflow: str | None = Field(None, description="Workflow name")
    ref: str | None = Field(None, description="Git ref")
    sha: str | None = Field(None, description="Commit SHA")

    model_config = {"extra": "forbid", "strict": True}


class Producer(BaseModel):
    """Producer metadata."""

    name: str = Field(..., description="Producer name (required, non-empty)")
    version: str = Field(..., description="Producer version (semver)")
    build: str | None = Field(None, description="Build identifier")

    model_config = {"extra": "forbid", "strict": True}

    @field_validator("name")
    @classmethod
    def name_must_be_non_empty(cls, v: str) -> str:
        """Validate that name is non-empty."""
        if not v or not v.strip():
            raise ValueError("name must be non-empty")
        return v


class AuditEnvelopeV1(BaseModel):
    """Audit Envelope v1.0."""

    schema_version: str = Field(..., description="Schema version (must be '1.0')")
    producer: Producer = Field(..., description="Producer metadata")
    run: Run = Field(..., description="Run metadata")
    source: Source = Field(..., description="Source metadata")
    trace: list[TraceStep] = Field(..., description="Trace steps")
    extensions: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Namespaced extensions (optional)"
    )

    model_config = {"extra": "forbid", "strict": True}

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_be_1_0(cls, v: str) -> str:
        """Validate that schema_version is '1.0'."""
        if v != "1.0":
            raise ValueError("schema_version must be '1.0'")
        return v
