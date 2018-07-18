Feature: Transaction workflow NORDEA

  Scenario: Trivial transfer
    Given lake is running
    And   wall is running
    And   tenant is NORDEA
    And   vault is running

    When  pasive EUR account mine is created
    Then  mine balance should be 0 EUR

    When  active EUR account theirs is created
    Then  theirs balance should be 0 EUR

    When  0.00000000001 EUR is transfered from mine to theirs
    Then  mine balance should be -0.00000000001 EUR
    And   theirs balance should be 0.00000000001 EUR

    When  0.00000000001 EUR is transfered from theirs to mine
    Then  mine balance should be 0 EUR
    And   theirs balance should be 0 EUR

  Scenario: tenant isolation
    Given lake is running
    And   mongo is running
    And   wall is running
    And   tenant is FIO
    And   vault is running

    When  pasive CZK account Nostro is created
    And   active CZK account Credit is created
    Then  Nostro should exist
    And   Credit should exist

    Given tenant is RAIFFEISEN
    And   vault is running

    Then  Nostro should not exist
    And   Credit should not exist

  Scenario: Transfer forward
    Given lake is running
    And   mongo is running
    And   wall is running
    And   tenant is AIRBANK
    And   vault is running

    When  active EUR account OriginCredit is created
    Then  OriginCredit balance should be 0 EUR

    When  pasive EUR account OriginDebit is created
    Then  OriginDebit balance should be 0 EUR

    When  active EUR account Target is created
    Then  Target balance should be 0 EUR

    When  Following transaction forward_id is created 1 times
    """
        OriginDebit OriginCredit 1 EUR transfer_1
        OriginDebit OriginCredit 2 EUR transfer_2
    """
    Then  OriginDebit balance should be -3 EUR
    And   OriginCredit balance should be 3 EUR
    And   Target balance should be 0 EUR

    When  forward_id transfer_1 credit side is forwarded to Target
    Then  OriginDebit balance should be -3 EUR
    And   OriginCredit balance should be 2 EUR
    And   Target balance should be 1 EUR

    When  forward_id transfer_2 credit side is forwarded to Target
    Then  OriginDebit balance should be -3 EUR
    And   OriginCredit balance should be 0 EUR
    And   Target balance should be 3 EUR

    When  forward_id transfer_1 debit side is forwarded to Target
    Then  OriginDebit balance should be -2 EUR
    And   OriginCredit balance should be 0 EUR
    And   Target balance should be 2 EUR

    When  forward_id transfer_2 debit side is forwarded to Target
    Then  OriginDebit balance should be 0 EUR
    And   OriginCredit balance should be 0 EUR
    And   Target balance should be 0 EUR
