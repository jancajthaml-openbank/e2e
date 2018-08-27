Feature: Integrity test

  Scenario: Replay same transaction
    Given appliance is running
    And   vault INTEGRITY is onbdoarded

    When  active EUR account INTEGRITY/ReplayCredit is created
    And   pasive EUR account INTEGRITY/ReplayDebit is created
    And   following transaction is created 100 times for tenant INTEGRITY
    """
      {
        "id": "race",
        "transfers": [{
          "id": "race_id_1",
          "credit": "ReplayCredit",
          "debit": "ReplayDebit",
          "amount": "1.0",
          "currency": "EUR"
        }, {
          "id": "race_id_2",
          "credit": "ReplayCredit",
          "debit": "ReplayDebit",
          "amount": "2.0",
          "currency": "EUR"
        }, {
          "id": "race_id_3",
          "credit": "ReplayCredit",
          "debit": "ReplayDebit",
          "amount": "3.0",
          "currency": "EUR"
        }]
      }
    """
    Then metrics for tenant INTEGRITY should report 2 created accounts
    And  metrics should report 3 created transfers
    And  INTEGRITY/ReplayCredit balance should be 6 EUR
    And  INTEGRITY/ReplayDebit balance should be -6 EUR
