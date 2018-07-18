Feature: Negative testing

  Scenario: setup
    Given wall is running

  Scenario: Account API - request for account of non-existant vault
    When  I call GET https://wall:443/account/nothing/xxx
    Then  response status should be 504
    And   response content should be:
    """
      {}
    """

