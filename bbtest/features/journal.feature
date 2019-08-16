Feature: Journal integrity test

  Scenario: setup
    Given appliance is running
    And   vault JOURNAL is onboarded
    And   ledger JOURNAL is onboarded

  Scenario: Creation of account
    When  pasive EUR account JOURNAL/Euro is created
    Then  snapshot JOURNAL/Euro version 0 should be
      | key            | value   |
      | version        |       0 |
      | balance        |       0 |
      | promised       |       0 |
      | promiseBuffer  |         |
      | accountName    |    Euro |
      | isBalanceCheck |   false |
      | format         |  BBTEST |
      | currency       |     EUR |

    When  active XRP account JOURNAL/Ripple is created
    Then  snapshot JOURNAL/Ripple version 0 should be
      | key            | value   |
      | version        |       0 |
      | balance        |       0 |
      | promised       |       0 |
      | promiseBuffer  |         |
      | accountName    |  Ripple |
      | isBalanceCheck |    true |
      | format         |  BBTEST |
      | currency       |     XRP |

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
      | credit    | debit     | amount                       | currency |
      | JOURNAL/B | JOURNAL/A | 123456789123313.000422901124 | XXX      |

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
      | credit    | debit     | amount                       | currency |
      | JOURNAL/C | JOURNAL/D | 123456789123313.000422901124 | XXX      |
    And   transaction yyy state of JOURNAL should be rollbacked
    And   directory /data/t_JOURNAL/account/C/events/0000000000 should contain 2 files
    And   file /data/t_JOURNAL/account/C/events/0000000000/0_123456789123313.000422901124_yyy should exist
    And   file /data/t_JOURNAL/account/C/events/0000000000/2_123456789123313.000422901124_yyy should exist
    And   directory /data/t_JOURNAL/account/D/events/0000000000 should contain 0 files
