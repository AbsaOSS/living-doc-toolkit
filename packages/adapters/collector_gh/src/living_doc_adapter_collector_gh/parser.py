# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""
Input parser for the collector-gh adapter.

This module provides functions to parse collector-gh output into
AdapterResult format.
"""

from living_doc_core.errors import AdapterError  # type: ignore[import-untyped]

from living_doc_adapter_collector_gh.compatibility import check_compatibility
from living_doc_adapter_collector_gh.detector import extract_version
from living_doc_adapter_collector_gh.models import (
    AdapterItem,
    AdapterItemTimestamps,
    AdapterMetadata,
    AdapterMetadataProducer,
    AdapterMetadataRun,
    AdapterMetadataSource,
    AdapterResult,
)


def parse(payload: dict) -> AdapterResult:
    """
    Parse collector-gh output into AdapterResult format.

    Args:
        payload: Input payload from collector-gh

    Returns:
        AdapterResult with parsed items and metadata

    Raises:
        AdapterError: If parsing fails
    """
    try:
        # Extract version and check compatibility
        version = extract_version(payload)
        warnings = check_compatibility(version)

        # Extract metadata
        metadata_dict = payload.get("metadata", {})
        generator = metadata_dict.get("generator", {})
        run = metadata_dict.get("run", {})
        source = metadata_dict.get("source", {})

        # Get source repository for constructing item IDs
        repositories = source.get("repositories", [])
        source_repo = repositories[0] if repositories else "unknown/repo"

        # Create metadata
        metadata = AdapterMetadata(
            producer=AdapterMetadataProducer(
                name=generator.get("name", ""),
                version=generator.get("version", ""),
                build=generator.get("build"),
            ),
            run=AdapterMetadataRun(
                run_id=run.get("run_id"),
                run_attempt=run.get("run_attempt"),
                actor=run.get("actor"),
                workflow=run.get("workflow"),
                ref=run.get("ref"),
                sha=run.get("sha"),
            ),
            source=AdapterMetadataSource(
                systems=source.get("systems", []),
                repositories=repositories,
                organization=source.get("organization"),
                enterprise=source.get("enterprise"),
            ),
            original_metadata=metadata_dict,
        )

        # Parse issues into adapter items
        # Support both dict format (keyed by issue ID) and list format
        issues_data = payload.get("issues", {})
        if isinstance(issues_data, dict):
            issues_list = list(issues_data.values())
        else:
            issues_list = issues_data if isinstance(issues_data, list) else []

        items = []
        for issue in issues_list:
            try:
                # Support both 'number' and 'issue_number' field names
                issue_number = issue.get("number") or issue.get("issue_number")
                item = AdapterItem(
                    id=f"github:{source_repo}#{issue_number}",
                    title=issue["title"],
                    state=issue["state"],
                    tags=issue.get("labels", []),
                    url=issue["html_url"],
                    timestamps=AdapterItemTimestamps(
                        created=issue["created_at"],
                        updated=issue["updated_at"],
                    ),
                    body=issue.get("body"),
                )
                items.append(item)
            except (KeyError, TypeError) as e:
                issue_number = issue.get("number") or issue.get("issue_number", "unknown")
                raise AdapterError(f"Failed to parse issue {issue_number}: {e}") from e

        return AdapterResult(items=items, metadata=metadata, warnings=warnings)

    except AdapterError:
        raise
    except Exception as e:
        raise AdapterError(f"Failed to parse collector-gh payload: {e}") from e
