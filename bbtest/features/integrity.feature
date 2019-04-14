Feature: Integrity test

  Scenario: Replay same transaction
    Given appliance is running
    And   vault INTEGRITY is onbdoarded
    And   ledger INTEGRITY is onbdoarded
    When  active EUR account INTEGRITY/ReplayCredit is created
    And   pasive EUR account INTEGRITY/ReplayDebit is created
    And   following transaction is created 100 times from tenant INTEGRITY
    """
      {
        "id": "race",
        "transfers": [
          {
            "id": "race_id_1",
            "credit": {
              "tenant": "INTEGRITY",
              "name": "ReplayCredit"
            },
            "debit": {
              "tenant": "INTEGRITY",
              "name": "ReplayDebit"
            },
            "amount": "1",
            "currency": "EUR"
          },
          {
            "id": "race_id_2",
            "credit": {
              "tenant": "INTEGRITY",
              "name": "ReplayCredit"
            },
            "debit": {
              "tenant": "INTEGRITY",
              "name": "ReplayDebit"
            },
            "amount": "2",
            "currency": "EUR"
          },
          {
            "id": "race_id_3",
            "credit": {
              "tenant": "INTEGRITY",
              "name": "ReplayCredit"
            },
            "debit": {
              "tenant": "INTEGRITY",
              "name": "ReplayDebit"
            },
            "amount": "3",
            "currency": "EUR"
          }
        ]
      }
    """
    Then  metrics for tenant INTEGRITY should report 2 created accounts
    And   INTEGRITY/ReplayCredit balance should be 6 EUR
    And   INTEGRITY/ReplayDebit balance should be -6 EUR
    #And   there should exist following transfers for tenant INTEGRITY
