# =============================================================================
# LIVING DOC — US-1 · User Login
# =============================================================================
# source:         https://github.com/absa-group/aul-ui/issues/2
# status:         active
# business_value:
#   - Users can reach the application securely.
# preconditions:
#   - The user has a registered account.
# acceptance_criteria:
#   AC:US-1-01 (v1.0.0 - Active)
#     - User can log in with valid credentials.
#   AC:US-1-02 (v1.0.0 - Active)
#     - Login button is disabled until both fields are filled.
#   AC:US-1-03 (v0.9.0 - Deprecated)
#     - Legacy basic-auth login (removed).
# =============================================================================

@US_ID:US-1
Feature: User Login
As a user, I want to log in so that I can access the application.

  @Regression @AC:US-1-01 @AC:US-1-02
  Scenario: User logs in with valid credentials
    Given the user is on the login page
    When the user fills in both fields with valid credentials
    Then the login button is enabled
    And submitting the form shows the dashboard

  @Smoke @AC:US-1-02
  Scenario: Login button stays disabled until fields are filled
    Given the user is on the login page
    Then the login button is disabled

  @Regression @skip @AC:US-1-03
  Scenario: Legacy basic-auth login
    Given the user sends a basic-auth header
    Then access is rejected

  @Regression @AC:US-1-99
  Scenario: Scenario referencing an AC that no longer exists
    Given a stale test
    Then it still runs
