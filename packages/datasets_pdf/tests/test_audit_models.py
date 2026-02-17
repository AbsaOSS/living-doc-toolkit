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
Unit tests for Audit Envelope v1 models.
"""

import pytest
from pydantic import ValidationError

from living_doc_datasets_pdf.audit.v1.models import (
    AuditEnvelopeV1,
    AuditWarning,
    Producer,
    Run,
    Source,
    TraceStep,
)
from living_doc_datasets_pdf.audit.v1.serializer import from_json, to_json


def test_valid_audit_envelope():
    """Test valid audit envelope instantiation."""
    data = {
        "schema_version": "1.0",
        "producer": {"name": "AbsaOSS/living-doc-collector-gh", "version": "1.2.0", "build": "abc123"},
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
            }
        ],
        "extensions": {},
    }

    envelope = AuditEnvelopeV1.model_validate(data)

    assert envelope.schema_version == "1.0"
    assert envelope.producer.name == "AbsaOSS/living-doc-collector-gh"
    assert envelope.producer.version == "1.2.0"
    assert envelope.producer.build == "abc123"
    assert envelope.run.run_id == "123456"
    assert envelope.source.systems == ["GitHub"]
    assert len(envelope.trace) == 1
    assert envelope.trace[0].step == "collection"


def test_invalid_schema_version():
    """Test that schema_version must be '1.0'."""
    data = {
        "schema_version": "2.0",
        "producer": {"name": "test", "version": "1.0.0"},
        "run": {},
        "source": {"systems": ["GitHub"]},
        "trace": [],
    }

    with pytest.raises(ValidationError) as exc_info:
        AuditEnvelopeV1.model_validate(data)

    assert "schema_version must be '1.0'" in str(exc_info.value)


def test_invalid_empty_producer_name():
    """Test that producer.name must be non-empty."""
    data = {
        "schema_version": "1.0",
        "producer": {"name": "", "version": "1.0.0"},
        "run": {},
        "source": {"systems": ["GitHub"]},
        "trace": [],
    }

    with pytest.raises(ValidationError) as exc_info:
        AuditEnvelopeV1.model_validate(data)

    assert "name must be non-empty" in str(exc_info.value)


def test_invalid_empty_systems():
    """Test that source.systems must be non-empty."""
    data = {
        "schema_version": "1.0",
        "producer": {"name": "test", "version": "1.0.0"},
        "run": {},
        "source": {"systems": []},
        "trace": [],
    }

    with pytest.raises(ValidationError) as exc_info:
        AuditEnvelopeV1.model_validate(data)

    assert "systems must be non-empty" in str(exc_info.value)


def test_missing_required_fields():
    """Test that missing required fields raise ValidationError."""
    data = {"schema_version": "1.0"}

    with pytest.raises(ValidationError):
        AuditEnvelopeV1.model_validate(data)


def test_extra_fields_forbidden():
    """Test that extra fields are forbidden."""
    data = {
        "schema_version": "1.0",
        "producer": {"name": "test", "version": "1.0.0"},
        "run": {},
        "source": {"systems": ["GitHub"]},
        "trace": [],
        "extra_field": "not allowed",
    }

    with pytest.raises(ValidationError) as exc_info:
        AuditEnvelopeV1.model_validate(data)

    assert "Extra inputs are not permitted" in str(exc_info.value)


def test_warning_model():
    """Test AuditWarning model."""
    warning = AuditWarning(code="VERSION_MISMATCH", message="Version mismatch detected", context="field.path")

    assert warning.code == "VERSION_MISMATCH"
    assert warning.message == "Version mismatch detected"
    assert warning.context == "field.path"


def test_trace_step_with_warnings():
    """Test TraceStep with warnings."""
    trace = TraceStep(
        step="normalization",
        tool="living-doc-toolkit",
        tool_version="0.1.0",
        started_at="2026-01-23T12:00:00Z",
        finished_at="2026-01-23T12:00:05Z",
        warnings=[AuditWarning(code="TEST", message="Test warning", context=None)],
    )

    assert trace.step == "normalization"
    assert len(trace.warnings) == 1
    assert trace.warnings[0].code == "TEST"


def test_serialization_round_trip():
    """Test serialization and deserialization round-trip."""
    data = {
        "schema_version": "1.0",
        "producer": {"name": "test", "version": "1.0.0", "build": None},
        "run": {"run_id": None, "run_attempt": None, "actor": None, "workflow": None, "ref": None, "sha": None},
        "source": {"systems": ["GitHub"], "repositories": [], "organization": None, "enterprise": None},
        "trace": [],
        "extensions": {},
    }

    envelope1 = AuditEnvelopeV1.model_validate(data)
    json_str = to_json(envelope1)
    envelope2 = from_json(json_str)

    assert envelope1.model_dump() == envelope2.model_dump()


def test_deterministic_serialization():
    """Test that serialization produces deterministic output."""
    envelope = AuditEnvelopeV1(
        schema_version="1.0",
        producer=Producer(name="test", version="1.0.0", build=None),
        run=Run(
            run_id=None,
            run_attempt=None,
            actor=None,
            workflow=None,
            ref=None,
            sha=None,
        ),
        source=Source(systems=["GitHub"], repositories=[], organization=None, enterprise=None),
        trace=[],
    )

    json1 = to_json(envelope)
    json2 = to_json(envelope)

    assert json1 == json2


def test_extensions_with_namespaced_data():
    """Test extensions with namespaced data."""
    data = {
        "schema_version": "1.0",
        "producer": {"name": "test", "version": "1.0.0"},
        "run": {},
        "source": {"systems": ["GitHub"]},
        "trace": [],
        "extensions": {"collector-gh": {"original_metadata": {"key": "value"}}, "builder": {"step": "normalize"}},
    }

    envelope = AuditEnvelopeV1.model_validate(data)

    assert "collector-gh" in envelope.extensions
    assert envelope.extensions["collector-gh"]["original_metadata"]["key"] == "value"
    assert envelope.extensions["builder"]["step"] == "normalize"
