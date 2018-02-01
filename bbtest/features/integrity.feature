Feature: Integrity test

  Background: Basic orchestration
    Given container wall should be running
    And   container lake should be running
    And   container vault should be running
    And   wall is listening on 8080
    And   wall is healthy
    And   storage is empty

  Scenario: Replay same transaction
    Given tenant is test

    When  active EUR account ReplayCredit is created
    When  pasive EUR account ReplayDredit is created

    When  Following transaction race is created 100 times
    """
        ReplayDredit ReplayCredit 1 EUR race_id
    """
