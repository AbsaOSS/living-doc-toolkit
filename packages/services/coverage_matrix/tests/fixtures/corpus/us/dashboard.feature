# =============================================================================
# LIVING DOC — US-2 · View Dashboard
# =============================================================================
# source:         https://github.com/absa-group/aul-ui/issues/5
# status:         active
# acceptance_criteria:
#   AC:US-2-01 (v1.0.0 - Active)
#     - User can see accessible domains on the dashboard.
#   AC:US-2-02 (v1.0.0 - Active)
#     - Dashboard shows an empty state when no domains are accessible.
# =============================================================================

@US_ID:US-2
Feature: View Dashboard
As a user, I want a dashboard overview.

  @Regression @AC:US-2-01
  Scenario: User sees accessible domains on the dashboard
    Given the user has accessible domains
    When the user opens the dashboard
    Then the accessible domains are listed
