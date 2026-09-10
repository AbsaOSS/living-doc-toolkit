# A scenario file tagged for a user story that is not part of the doc-source input.
# doc-source skips it (no header block); ui-tests mines the scenario with us_id US-99,
# which the coverage matcher cannot resolve -> unlinked test.

@US_ID:US-99
Feature: Scenario for an unknown user story

  @Regression @AC:US-99-01
  Scenario: Scenario for a user story not in the doc input
    Given a test for an unknown story
    Then it lands in unlinked tests
