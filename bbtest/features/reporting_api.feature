Feature: Reporting API test

  Scenario: Account search
    Given lake is running
    And   mongo is running
    And   wall is running
    And   tenant is GRAPH
    And   vault is running
    And   reporting is running
    And   pasive EUR account Sample is created

    When I request reporting
      """
        Accounts {
          name
        }
      """
    Then reporting responds with
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
