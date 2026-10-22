# Copyright 2026 ABSA Group Limited. Apache License, Version 2.0.

"""Tests that the `normalize-tests` lineage table covers the pinned contract."""

from living_doc_utilities.contracts.lineage import assert_complete

from living_doc_service_normalize_tests.lineage import LINEAGE_TABLE


def test_the_lineage_table_accounts_for_every_ui_tests_field():
    assert_complete(LINEAGE_TABLE, "ui-tests-v1.0.0")
    assert len(LINEAGE_TABLE.entries) == 12
