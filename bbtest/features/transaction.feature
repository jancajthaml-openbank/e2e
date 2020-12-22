Feature: Transaction workflow

  Scenario: Setup
    Given appliance is running
    And   vault NORDEA is onboarded
    And   ledger NORDEA is onboarded
    And   vault FIO is onboarded
    And   ledger FIO is onboarded
    And   vault AIRBANK is onboarded
    And   ledger AIRBANK is onboarded
    And   vault RAIFFEISEN is onboarded
    And   ledger RAIFFEISEN is onboarded

  Scenario: Trivial transfer
    When  pasive EUR account NORDEA/mine is created
    Then  NORDEA/mine balance should be 0.0 EUR

    When  active EUR account NORDEA/theirs is created
    Then  NORDEA/theirs balance should be 0.0 EUR

    When  0.00000000001 EUR is transferred from NORDEA/mine to NORDEA/theirs
    Then  NORDEA/mine balance should be -0.00000000001 EUR
    And   NORDEA/theirs balance should be 0.00000000001 EUR

    When  0.00000000001 EUR is transferred from NORDEA/theirs to NORDEA/mine
    Then  NORDEA/mine balance should be 0.0 EUR
    And   NORDEA/theirs balance should be 0.0 EUR

  Scenario: Tenant isolation
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
    Then  RAIFFEISEN/Nostro balance should be 0.0 CZK
    Then  RAIFFEISEN/Nostro balance should be 0.0 CZK
