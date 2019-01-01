Feature: Journal integrity test

  Scenario: setup
    Given appliance is running
    And   vault JOURNAL is onbdoarded

  Scenario: Creation of account
    When  pasive EUR account JOURNAL/Euro is created
    Then  snapshot JOURNAL/Euro version 0 should be
    """
      {
        "version": 0,
        "accountName": "Euro",
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
        "accountName": "Ripple",
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
    And   following transaction is created for tenant JOURNAL
    """
      {
        "id": "xxx",
        "transfers": [
          {
            "credit": "B",
            "debit": "A",
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
            "credit": "B",
            "debit": "A",
            "amount": "123456789123313.000422901124",
            "currency": "XXX"
          }
        ]
      }
    """
    And   transaction xxx state of JOURNAL should be committed
    And   directory /data/JOURNAL/account/A/events/0000000000 should contain 2 files
    And   file /data/JOURNAL/account/A/events/0000000000/0_-123456789123313.000422901124_xxx should exist
    And   file /data/JOURNAL/account/A/events/0000000000/1_-123456789123313.000422901124_xxx should exist
    And   directory /data/JOURNAL/account/B/events/0000000000 should contain 2 files
    And   file /data/JOURNAL/account/B/events/0000000000/0_123456789123313.000422901124_xxx should exist
    And   file /data/JOURNAL/account/B/events/0000000000/1_123456789123313.000422901124_xxx should exist

  Scenario: Creating of transaction rejected (insufficient funds)
    When  pasive XXX account JOURNAL/C is created
    And   active XXX account JOURNAL/D is created
    And   following transaction is created for tenant JOURNAL
    """
      {
        "id": "yyy",
        "transfers": [
          {
            "credit": "C",
            "debit": "D",
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
            "credit": "C",
            "debit": "D",
            "amount": "123456789123313.000422901124",
            "currency": "XXX"
          }
        ]
      }
    """
    And   transaction yyy state of JOURNAL should be rollbacked
    And   directory /data/JOURNAL/account/C/events/0000000000 should contain 2 files
    And   file /data/JOURNAL/account/C/events/0000000000/0_123456789123313.000422901124_yyy should exist
    And   file /data/JOURNAL/account/C/events/0000000000/2_123456789123313.000422901124_yyy should exist
    And   directory /data/JOURNAL/account/D/events/0000000000 should contain 0 files
