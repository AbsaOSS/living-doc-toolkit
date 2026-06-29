# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for the schema_export module."""

import json
import tempfile
from pathlib import Path

from living_doc_adapter_collector_gh.schema_export import export_schema, get_default_schema_path, get_schema_version


class TestGetSchemaVersion:
    """Tests for get_schema_version."""

    def test_returns_semver_string(self):
        """Test that get_schema_version returns a semver string."""
        version = get_schema_version()
        assert isinstance(version, str)
        parts = version.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)


class TestGetDefaultSchemaPath:
    """Tests for get_default_schema_path."""

    def test_returns_path_ending_in_schemas(self):
        """Test that the default schema path ends with 'schemas/'."""
        path = get_default_schema_path()
        assert isinstance(path, Path)
        assert path.name == "schemas"

    def test_path_is_within_collector_gh(self):
        """Test that the path resolves inside the collector_gh package."""
        path = get_default_schema_path()
        assert "collector_gh" in str(path)


class TestExportSchema:
    """Tests for export_schema."""

    def test_export_schema_to_custom_path(self):
        """Test exporting schema to a custom temporary path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "test-schema.json"
            schema = export_schema(output)

            assert isinstance(schema, dict)
            assert output.exists()

            with open(output, encoding="utf-8") as f:
                loaded = json.load(f)

            assert loaded == schema
            assert "$schema_version" in schema

    def test_export_schema_returns_dict(self):
        """Test that export_schema returns a dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "schema.json"
            result = export_schema(output)
            assert isinstance(result, dict)
