# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Pydantic models for the collector-gh adapter — a consumer-side representation of the
`doc-issues.json` input contract.

`living-doc-collector-gh` owns this contract: since its PR #110 it generates
`doc-issues-v1.0.0-schema.json` from its own `doc_issues/models.py`, and this repo vendors
a pinned copy of that schema under `schemas/`. The models below mirror the vendored schema
(field list identical to collector-gh's `doc_issues/models.py`) and are kept in step with it
via the golden-fixture tests — they are not the source of truth for what a valid
`doc-issues.json` looks like.

See SCHEMA_SYNC.md for the synchronization workflow.
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


class AcceptanceCriterion(BaseModel):
    """A single acceptance-criterion row parsed from an issue body."""

    id: str
    state: str
    version: str
    description: str


class AdapterItem(BaseModel):
    """A single consolidated issue enriched with parsed body sections."""

    id: str
    title: str
    state: str
    tags: list[str]
    url: str
    timestamps: AdapterItemTimestamps
    description: str | None = None
    business_value: list[str] | None = None
    preconditions: list[str] | None = None
    acceptance_criteria: list[AcceptanceCriterion] | None = None


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

    # `items` holds every collected documentation record regardless of source system or
    # documentation type — there is no per-type grouping and no `type` field on the item;
    # the type is carried by the `DocumentedUserStory` / `DocumentedFeature` /
    # `DocumentedFunctionality` label in `AdapterItem.tags`. Mirrors the top-level array in
    # collector-gh's `doc_issues/models.py`.
    items: list[AdapterItem]
    metadata: AdapterMetadata
    warnings: list[CompatibilityWarning]
