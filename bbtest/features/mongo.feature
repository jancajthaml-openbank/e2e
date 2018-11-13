Feature: Mongo integrity

  Scenario: setup
    Given appliance is running
    And   vault MONGO is onbdoarded

  Scenario: Trivial transfer
    When  pasive EUR account MONGO/mine is created
    And   active EUR account MONGO/theirs is created
    And   0.00000000001 EUR is transfered from mine to theirs for tenant MONGO
    And   0.00000000001 EUR is transfered from theirs to mine for tenant MONGO

    Then mongo collection account should contain
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
