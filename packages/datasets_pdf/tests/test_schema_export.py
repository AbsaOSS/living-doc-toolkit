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

from living_doc_datasets_pdf.audit.v1.schema import export_json_schema as export_audit_schema
from living_doc_datasets_pdf.pdf_ready.v1.schema import export_json_schema as export_pdf_ready_schema


def test_export_audit_schema_returns_dict():
    """Test that export_audit_schema returns a dictionary."""
    schema = export_audit_schema()

    assert isinstance(schema, dict)
    assert "$defs" in schema or "properties" in schema


def test_export_pdf_ready_schema_returns_dict():
    """Test that export_pdf_ready_schema returns a dictionary."""
    schema = export_pdf_ready_schema()

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


def test_export_pdf_ready_schema_to_file(tmp_path):
    """Test that export_pdf_ready_schema writes to file."""
    output_path = tmp_path / "pdf_ready_test.schema.json"

    schema = export_pdf_ready_schema(output_path)

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
