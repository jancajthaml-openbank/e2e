Feature: Negative testing

  Scenario: setup
    Given appliance is running
    And   vault NEGATIVE is onbdoarded

  Scenario: Account API - request for account of non-existant vault
    When I request wall GET /account/nothing/xxx
    Then wall responds with 504
    """
      {}
    """
