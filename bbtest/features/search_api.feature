Feature: Search API test

  Scenario: setup
    Given appliance is running
    And   vault SEARCH is onbdoarded

  Scenario: Accounts query
    When  active EUR account SEARCH/ReplayCredit is created
    And   pasive EUR account SEARCH/ReplayDebit is created

    When I request search
    """
      Accounts(tenant: "SEARCH") {
        name
        currency
      }
    """
    Then search responds with 200
    """
      {
        "data": {
          "Accounts": [
            {
              "name": "ReplayCredit",
              "currency": "EUR"
            },
            {
              "name": "ReplayDebit",
              "currency": "EUR"
            }
          ]
        }
      }
    """


