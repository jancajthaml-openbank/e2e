Feature: Mongo integrity

  Scenario: setup
    Given appliance is running
    And   vault MONGO is onbdoarded
    And   ledger MONGO is onbdoarded

  Scenario: Trivial transfer
    When  pasive EUR account MONGO/mine is created
    And   active EUR account MONGO/theirs is created
    And   0.00000000001 EUR is transferred from MONGO/mine to MONGO/theirs
    And   0.00000000001 EUR is transferred from MONGO/theirs to MONGO/mine

    Then  mongo collection account should contain
      """
        [
          {
            "_id": "MONGO/mine",
            "tenant": "MONGO",
            "name": "mine",
            "currency": "EUR"
          },
          {
            "_id": "MONGO/theirs",
            "tenant": "MONGO",
            "name": "theirs",
            "currency": "EUR"
          }
        ]
      """
