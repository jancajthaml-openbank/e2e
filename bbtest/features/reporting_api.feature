Feature: Search API test

  Scenario: Account search
    Given lake is running
    And   mongo is running
    And   wall is running
    And   tenant is GRAPH
    And   vault is running
    And   search is running
    And   pasive EUR account Sample is created

    When I request search
      """
        Accounts {
          name
        }
      """
    Then search responds with
      """
        {
          "data": {
            "Accounts": [
              {
                "name": "Sample"
              }
            ]
          }
        }
      """
