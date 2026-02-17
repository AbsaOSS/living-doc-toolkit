# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for the detector module."""

import pytest
from living_doc_core.errors import AdapterError

from living_doc_adapter_collector_gh.detector import can_handle, extract_version


class TestCanHandle:
    """Tests for the can_handle function."""

    def test_can_handle_valid_collector_gh_payload(self):
        """Test that can_handle returns True for valid collector-gh payload."""
        payload = {"metadata": {"generator": {"name": "AbsaOSS/living-doc-collector-gh", "version": "1.0.0"}}}
        assert can_handle(payload) is True

    def test_can_handle_different_generator_name(self):
        """Test that can_handle returns False for different generator name."""
        payload = {"metadata": {"generator": {"name": "different-generator", "version": "1.0.0"}}}
        assert can_handle(payload) is False

    def test_can_handle_missing_metadata(self):
        """Test that can_handle returns False when metadata is missing."""
        payload = {}
        assert can_handle(payload) is False

    def test_can_handle_missing_generator(self):
        """Test that can_handle returns False when generator is missing."""
        payload = {"metadata": {}}
        assert can_handle(payload) is False

    def test_can_handle_missing_name(self):
        """Test that can_handle returns False when name is missing."""
        payload = {"metadata": {"generator": {"version": "1.0.0"}}}
        assert can_handle(payload) is False

    def test_can_handle_empty_dict(self):
        """Test that can_handle returns False for empty dictionary."""
        assert can_handle({}) is False

    def test_can_handle_null_generator(self):
        """Test that can_handle returns False when generator is None."""
        payload = {"metadata": {"generator": None}}
        assert can_handle(payload) is False


class TestExtractVersion:
    """Tests for the extract_version function."""

    def test_extract_version_valid_payload(self):
        """Test that extract_version returns version string from valid payload."""
        payload = {"metadata": {"generator": {"name": "AbsaOSS/living-doc-collector-gh", "version": "1.2.3"}}}
        version = extract_version(payload)
        assert version == "1.2.3"

    def test_extract_version_missing_metadata(self):
        """Test that extract_version raises AdapterError when metadata is missing."""
        payload = {}
        with pytest.raises(AdapterError) as exc_info:
            extract_version(payload)
        assert "metadata.generator.version" in str(exc_info.value)

    def test_extract_version_missing_generator(self):
        """Test that extract_version raises AdapterError when generator is missing."""
        payload = {"metadata": {}}
        with pytest.raises(AdapterError) as exc_info:
            extract_version(payload)
        assert "metadata.generator.version" in str(exc_info.value)

    def test_extract_version_missing_version(self):
        """Test that extract_version raises AdapterError when version is missing."""
        payload = {"metadata": {"generator": {"name": "AbsaOSS/living-doc-collector-gh"}}}
        with pytest.raises(AdapterError) as exc_info:
            extract_version(payload)
        assert "metadata.generator.version" in str(exc_info.value)

    def test_extract_version_empty_version(self):
        """Test that extract_version raises AdapterError when version is empty."""
        payload = {"metadata": {"generator": {"name": "AbsaOSS/living-doc-collector-gh", "version": ""}}}
        with pytest.raises(AdapterError) as exc_info:
            extract_version(payload)
        assert "empty" in str(exc_info.value).lower()

    def test_extract_version_null_generator(self):
        """Test that extract_version raises AdapterError when generator is None."""
        payload = {"metadata": {"generator": None}}
        with pytest.raises(AdapterError) as exc_info:
            extract_version(payload)
        assert "metadata.generator.version" in str(exc_info.value)
