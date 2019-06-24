Feature: Journal integrity test

  Scenario: setup
    Given appliance is running
    And   vault JOURNAL is onbdoarded
    And   ledger JOURNAL is onbdoarded

  Scenario: Creation of account
    When  pasive EUR account JOURNAL/Euro is created
    Then  snapshot JOURNAL/Euro version 0 should be
    """
      {
        "version": 0,
        "name": "Euro",
        "format": "BBTEST",
        "isBalanceCheck": false,
        "currency": "EUR",
        "balance": "0",
        "promised": "0",
        "promiseBuffer": []
      }
    """

    When  active XRP account JOURNAL/Ripple is created
    Then  snapshot JOURNAL/Ripple version 0 should be
    """
      {
        "version": 0,
        "name": "Ripple",
        "format": "BBTEST",
        "isBalanceCheck": true,
        "currency": "XRP",
        "balance": "0",
        "promised": "0",
        "promiseBuffer": []
      }
    """

  Scenario: Creating of transaction comitted
    When  pasive XXX account JOURNAL/A is created
    And   active XXX account JOURNAL/B is created
    And   following transaction is created from tenant JOURNAL
    """
      {
        "id": "xxx",
        "transfers": [
          {
            "credit": {
              "tenant": "JOURNAL",
              "name": "B"
            },
            "debit": {
              "tenant": "JOURNAL",
              "name": "A"
            },
            "amount": "123456789123313.000422901124",
            "currency": "XXX"
          }
        ]
      }
    """
    Then  transaction xxx of JOURNAL should be
    """
      {
        "id": "xxx",
        "transfers": [
          {
            "credit": {
              "tenant": "JOURNAL",
              "name": "B"
            },
            "debit": {
              "tenant": "JOURNAL",
              "name": "A"
            },
            "amount": "123456789123313.000422901124",
            "currency": "XXX"
          }
        ]
      }
    """
    And   transaction xxx state of JOURNAL should be committed
    And   directory /data/t_JOURNAL/account/A/events/0000000000 should contain 2 files
    And   file /data/t_JOURNAL/account/A/events/0000000000/0_-123456789123313.000422901124_xxx should exist
    And   file /data/t_JOURNAL/account/A/events/0000000000/1_-123456789123313.000422901124_xxx should exist
    And   directory /data/t_JOURNAL/account/B/events/0000000000 should contain 2 files
    And   file /data/t_JOURNAL/account/B/events/0000000000/0_123456789123313.000422901124_xxx should exist
    And   file /data/t_JOURNAL/account/B/events/0000000000/1_123456789123313.000422901124_xxx should exist

  Scenario: Creating of transaction rejected (insufficient funds)
    When  pasive XXX account JOURNAL/C is created
    And   active XXX account JOURNAL/D is created
    And   following transaction is created from tenant JOURNAL
    """
      {
        "id": "yyy",
        "transfers": [
          {
            "credit": {
              "tenant": "JOURNAL",
              "name": "C"
            },
            "debit": {
              "tenant": "JOURNAL",
              "name": "D"
            },
            "amount": "123456789123313.000422901124",
            "currency": "XXX"
          }
        ]
      }
    """
    Then  transaction yyy of JOURNAL should be
    """
      {
        "id": "yyy",
        "transfers": [
          {
            "credit": {
              "tenant": "JOURNAL",
              "name": "C"
            },
            "debit": {
              "tenant": "JOURNAL",
              "name": "D"
            },
            "amount": "123456789123313.000422901124",
            "currency": "XXX"
          }
        ]
      }
    """
    And   transaction yyy state of JOURNAL should be rollbacked
    And   directory /data/t_JOURNAL/account/C/events/0000000000 should contain 2 files
    And   file /data/t_JOURNAL/account/C/events/0000000000/0_123456789123313.000422901124_yyy should exist
    And   file /data/t_JOURNAL/account/C/events/0000000000/2_123456789123313.000422901124_yyy should exist
    And   directory /data/t_JOURNAL/account/D/events/0000000000 should contain 0 files
