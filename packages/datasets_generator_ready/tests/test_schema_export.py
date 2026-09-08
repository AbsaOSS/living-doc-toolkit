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
Unit tests for JSON schema export functions.
"""

import json
from pathlib import Path

import jsonschema
import pytest

from living_doc_datasets_generator_ready.audit.v1.schema import export_json_schema as export_audit_schema
from living_doc_datasets_generator_ready.generator_ready.v1.schema import (
    export_json_schema as export_generator_ready_schema,
)

_COMMITTED_SCHEMA = Path(__file__).resolve().parents[1] / "schemas" / "generator-ready-v1.0.0-schema.json"


def test_export_audit_schema_returns_dict():
    """Test that export_audit_schema returns a dictionary."""
    schema = export_audit_schema()

    assert isinstance(schema, dict)
    assert "$defs" in schema or "properties" in schema


def test_export_generator_ready_schema_returns_dict():
    """Test that export_generator_ready_schema returns a dictionary."""
    schema = export_generator_ready_schema()

    assert isinstance(schema, dict)
    assert "$defs" in schema or "properties" in schema


def test_export_audit_schema_to_file(tmp_path):
    """Test that export_audit_schema writes to file."""
    output_path = tmp_path / "audit_test.schema.json"

    schema = export_audit_schema(output_path)

    assert output_path.exists()

    with open(output_path, encoding="utf-8") as f:
        loaded_schema = json.load(f)

    assert schema == loaded_schema


def test_export_generator_ready_schema_to_file(tmp_path):
    """Test that export_generator_ready_schema writes to file."""
    output_path = tmp_path / "generator_ready_test.schema.json"

    schema = export_generator_ready_schema(output_path)

    assert output_path.exists()

    with open(output_path, encoding="utf-8") as f:
        loaded_schema = json.load(f)

    assert schema == loaded_schema


def test_export_schema_creates_parent_directory(tmp_path):
    """Test that export_schema creates parent directories."""
    output_path = tmp_path / "nested" / "dir" / "schema.json"

    export_audit_schema(output_path)

    assert output_path.exists()
    assert output_path.parent.exists()


def test_committed_generator_ready_schema_is_in_sync():
    """The committed generator-ready schema file must match the model export."""
    with open(_COMMITTED_SCHEMA, encoding="utf-8") as f:
        committed = json.load(f)

    assert committed == export_generator_ready_schema()


def test_generator_ready_schema_constrains_schema_version():
    """The exported schema must enumerate the only accepted schema_version values."""
    schema = export_generator_ready_schema()

    assert schema["properties"]["schema_version"]["enum"] == ["generator-ready-v1.0.0", "1.0"]


def _valid_generator_ready_document(schema_version: str) -> dict:
    return {
        "schema_version": schema_version,
        "meta": {
            "document_title": "Test",
            "document_version": "1.0",
            "generated_at": "2026-01-23T12:00:00Z",
            "source_set": ["test"],
            "selection_summary": {"total_items": 0, "included_items": 0, "excluded_items": 0},
        },
        "content": {"user_stories": []},
    }


@pytest.mark.parametrize("schema_version", ["generator-ready-v1.0.0", "1.0"])
def test_schema_accepts_supported_schema_versions(schema_version):
    """JSON Schema validation passes for the canonical and deprecated values."""
    jsonschema.validate(_valid_generator_ready_document(schema_version), export_generator_ready_schema())


@pytest.mark.parametrize("schema_version", ["2.0", "generator-ready-v2.0.0", ""])
def test_schema_rejects_unsupported_schema_versions(schema_version):
    """JSON Schema validation fails for any value the models would reject."""
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_valid_generator_ready_document(schema_version), export_generator_ready_schema())
