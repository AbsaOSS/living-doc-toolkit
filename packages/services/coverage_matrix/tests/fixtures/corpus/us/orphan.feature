# A scenario file with no LIVING DOC header block and no @US_ID tag.
# doc-source skips it (no header); ui-tests mines the scenario as unlinked.

Feature: Orphan scenarios

  Scenario: Scenario not linked to any user story
    Given an unlabelled test
    Then it produces an unlinked entry
