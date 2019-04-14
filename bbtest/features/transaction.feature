Feature: Transaction workflow

  Scenario: setup
    Given appliance is running
    And   vault NORDEA is onbdoarded
    And   ledger NORDEA is onbdoarded
    And   vault FIO is onbdoarded
    And   ledger FIO is onbdoarded
    And   vault AIRBANK is onbdoarded
    And   ledger AIRBANK is onbdoarded
    And   vault RAIFFEISEN is onbdoarded
    And   ledger RAIFFEISEN is onbdoarded

  Scenario: Trivial transfer
    When  pasive EUR account NORDEA/mine is created
    Then  NORDEA/mine balance should be 0 EUR

    When  active EUR account NORDEA/theirs is created
    Then  NORDEA/theirs balance should be 0 EUR

    When  0.00000000001 EUR is transferred from NORDEA/mine to NORDEA/theirs
    Then  NORDEA/mine balance should be -0.00000000001 EUR
    And   NORDEA/theirs balance should be 0.00000000001 EUR

    When  0.00000000001 EUR is transferred from NORDEA/theirs to NORDEA/mine
    Then  NORDEA/mine balance should be 0 EUR
    And   NORDEA/theirs balance should be 0 EUR

  Scenario: tenant isolation
    When  pasive CZK account FIO/Nostro is created
    And   active CZK account FIO/Credit is created
    Then  FIO/Nostro should exist
    And   FIO/Credit should exist

    Then  RAIFFEISEN/Nostro should not exist
    And   RAIFFEISEN/Credit should not exist
    When  pasive CZK account RAIFFEISEN/Nostro is created
    And   active CZK account RAIFFEISEN/Credit is created
    Then  RAIFFEISEN/Nostro should exist
    And   RAIFFEISEN/Credit should exist

    When  1 CZK is transferred from FIO/Nostro to FIO/Credit
    Then  FIO/Nostro balance should be -1 CZK
    Then  FIO/Credit balance should be 1 CZK
    Then  RAIFFEISEN/Nostro balance should be 0 CZK
    Then  RAIFFEISEN/Nostro balance should be 0 CZK

  Scenario: Transfer forward
    When  active EUR account AIRBANK/OriginCredit is created
    Then  AIRBANK/OriginCredit balance should be 0 EUR

    When  pasive EUR account AIRBANK/OriginDebit is created
    Then  AIRBANK/OriginDebit balance should be 0 EUR

    When  active EUR account AIRBANK/Target is created
    Then  AIRBANK/Target balance should be 0 EUR

    When  following transaction is created from tenant AIRBANK
    """
      {
        "id": "forward_id",
        "transfers": [
          {
            "id": "transfer_1",
            "credit": {
              "tenant": "AIRBANK",
              "name": "OriginCredit"
            },
            "debit": {
              "tenant": "AIRBANK",
              "name": "OriginDebit"
            },
            "amount": "1",
            "currency": "EUR"
          },
          {
            "id": "transfer_2",
            "credit": {
              "tenant": "AIRBANK",
              "name": "OriginCredit"
            },
            "debit": {
              "tenant": "AIRBANK",
              "name": "OriginDebit"
            },
            "amount": "2",
            "currency": "EUR"
          }
        ]
      }
    """
    Then  AIRBANK/OriginDebit balance should be -3 EUR
    And   AIRBANK/OriginCredit balance should be 3 EUR
    And   AIRBANK/Target balance should be 0 EUR

    When  forward_id transfer_1 credit side is forwarded to AIRBANK/Target from tenant AIRBANK
    Then  AIRBANK/OriginDebit balance should be -3 EUR
    And   AIRBANK/OriginCredit balance should be 2 EUR
    And   AIRBANK/Target balance should be 1 EUR

    When  forward_id transfer_2 credit side is forwarded to AIRBANK/Target from tenant AIRBANK
    Then  AIRBANK/OriginDebit balance should be -3 EUR
    And   AIRBANK/OriginCredit balance should be 0 EUR
    And   AIRBANK/Target balance should be 3 EUR

    When  forward_id transfer_1 debit side is forwarded to AIRBANK/Target from tenant AIRBANK
    Then  AIRBANK/OriginDebit balance should be -2 EUR
    And   AIRBANK/OriginCredit balance should be 0 EUR
    And   AIRBANK/Target balance should be 2 EUR

    When  forward_id transfer_2 debit side is forwarded to AIRBANK/Target from tenant AIRBANK
    Then  AIRBANK/OriginDebit balance should be 0 EUR
    And   AIRBANK/OriginCredit balance should be 0 EUR
    And   AIRBANK/Target balance should be 0 EUR
