# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Pydantic models for the collector-gh adapter.

These models represent the output structure from the adapter after parsing
input from the living-doc-collector-gh action.
"""

from pydantic import BaseModel


class CompatibilityWarning(BaseModel):
    """Represents a compatibility warning during adapter processing."""

    code: str
    message: str
    context: str | None = None


class AdapterItemTimestamps(BaseModel):
    """Timestamps for an adapter item."""

    created: str
    updated: str


class AdapterItem(BaseModel):
    """Represents a single item (issue) from the collector output."""

    id: str
    title: str
    state: str
    tags: list[str]
    url: str
    timestamps: AdapterItemTimestamps
    body: str | None = None


class AdapterMetadataProducer(BaseModel):
    """Producer information for adapter metadata."""

    name: str
    version: str
    build: str | None


class AdapterMetadataRun(BaseModel):
    """Run information for adapter metadata."""

    run_id: str | None
    run_attempt: str | None
    actor: str | None
    workflow: str | None
    ref: str | None
    sha: str | None


class AdapterMetadataSource(BaseModel):
    """Source information for adapter metadata."""

    systems: list[str]
    repositories: list[str]
    organization: str | None
    enterprise: str | None


class AdapterMetadata(BaseModel):
    """Metadata information from the adapter."""

    producer: AdapterMetadataProducer
    run: AdapterMetadataRun
    source: AdapterMetadataSource
    original_metadata: dict


class AdapterResult(BaseModel):
    """Complete result from adapter parsing."""

    items: list[AdapterItem]
    metadata: AdapterMetadata
    warnings: list[CompatibilityWarning]
