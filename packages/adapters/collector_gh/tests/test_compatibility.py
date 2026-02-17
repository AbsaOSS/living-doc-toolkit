# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Unit tests for the compatibility module."""

from living_doc_adapter_collector_gh.compatibility import check_compatibility


class TestCheckCompatibility:
    """Tests for the check_compatibility function."""

    def test_version_1_0_0_no_warnings(self):
        """Test that version 1.0.0 produces no warnings."""
        warnings = check_compatibility("1.0.0")
        assert len(warnings) == 0

    def test_version_1_5_0_no_warnings(self):
        """Test that version 1.5.0 produces no warnings."""
        warnings = check_compatibility("1.5.0")
        assert len(warnings) == 0

    def test_version_1_9_9_no_warnings(self):
        """Test that version 1.9.9 produces no warnings."""
        warnings = check_compatibility("1.9.9")
        assert len(warnings) == 0

    def test_version_0_9_0_warning(self):
        """Test that version 0.9.0 produces VERSION_MISMATCH warning."""
        warnings = check_compatibility("0.9.0")
        assert len(warnings) == 1
        assert warnings[0].code == "VERSION_MISMATCH"
        assert "0.9.0" in warnings[0].message
        assert ">=1.0.0,<2.0.0" in warnings[0].message
        assert warnings[0].context == "metadata.generator.version"

    def test_version_2_0_0_warning(self):
        """Test that version 2.0.0 produces VERSION_MISMATCH warning."""
        warnings = check_compatibility("2.0.0")
        assert len(warnings) == 1
        assert warnings[0].code == "VERSION_MISMATCH"
        assert "2.0.0" in warnings[0].message
        assert ">=1.0.0,<2.0.0" in warnings[0].message
        assert warnings[0].context == "metadata.generator.version"

    def test_version_2_1_0_warning(self):
        """Test that version 2.1.0 produces VERSION_MISMATCH warning."""
        warnings = check_compatibility("2.1.0")
        assert len(warnings) == 1
        assert warnings[0].code == "VERSION_MISMATCH"
        assert "2.1.0" in warnings[0].message

    def test_version_3_0_0_warning(self):
        """Test that version 3.0.0 produces VERSION_MISMATCH warning."""
        warnings = check_compatibility("3.0.0")
        assert len(warnings) == 1
        assert warnings[0].code == "VERSION_MISMATCH"

    def test_invalid_version_string(self):
        """Test that invalid version string produces INVALID_VERSION warning."""
        warnings = check_compatibility("not-a-version")
        assert len(warnings) == 1
        assert warnings[0].code == "INVALID_VERSION"
        assert "not-a-version" in warnings[0].message
        assert warnings[0].context == "metadata.generator.version"

    def test_empty_version_string(self):
        """Test that empty version string produces INVALID_VERSION warning."""
        warnings = check_compatibility("")
        assert len(warnings) == 1
        assert warnings[0].code == "INVALID_VERSION"

    def test_version_with_prerelease(self):
        """Test that version with prerelease tag is handled correctly."""
        warnings = check_compatibility("1.5.0-alpha")
        assert len(warnings) == 0

    def test_version_with_build_metadata(self):
        """Test that version with build metadata is handled correctly."""
        warnings = check_compatibility("1.5.0+build.123")
        assert len(warnings) == 0

    def test_version_at_lower_boundary(self):
        """Test that version at exact lower boundary (1.0.0) has no warnings."""
        warnings = check_compatibility("1.0.0")
        assert len(warnings) == 0

    def test_version_just_below_upper_boundary(self):
        """Test that version just below upper boundary (1.999.999) has no warnings."""
        warnings = check_compatibility("1.999.999")
        assert len(warnings) == 0
