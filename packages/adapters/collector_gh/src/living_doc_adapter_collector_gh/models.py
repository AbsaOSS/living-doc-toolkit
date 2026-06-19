# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Pydantic models for the collector-gh adapter.

These models represent the authoritative input contract for doc-issues.json.
They are the single source of truth for the schema between this repository
(data consumer / schema producer) and the collector-gh repository
(data producer / schema consumer).

PYDANTIC-FIRST PATTERN
======================

This repo:
- Defines Pydantic models (source of truth)
- Exports them as JSON Schema for the collector-gh repo to use for validation

Collector-gh repo:
- Uses our exported JSON Schema to validate doc-issues.json
- Publishes validated data to us

To export schema for collector-gh:
    python -m living_doc_adapter_collector_gh.schema_export > doc-issues-schema.json

See SCHEMA_SYNC.md for the full synchronization workflow.
"""

from pydantic import BaseModel, Field


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
