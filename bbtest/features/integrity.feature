Feature: Integrity test

  Scenario: Replay same transaction
    Given lake is running
    And   wall is running
    And   tenant is INTEGRITY
    And   vault is running

    When  active EUR account ReplayCredit is created
    When  pasive EUR account ReplayDredit is created
    Then  metrics should report 2 created accounts

    When Following transaction race is created 100 times
    """
        ReplayDredit ReplayCredit 1 EUR race_id
    """
    Then metrics events should cancel out
    And  metrics should report 2 created accounts
