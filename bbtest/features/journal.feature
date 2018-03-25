Feature: Journal integrity test

  Background: Appliance
    Given lake is running
    And   mongo is running
    And   wall is running
    And   tenant is JOURNAL
    And   vault is running

  Scenario: Creation of account
    When  pasive EUR account Euro is created
    Then  snapshot /account/Euro/snapshot/0000000000 should be
    """
        {
            "version": 0,
            "balance": 0,
            "promised": 0,
            "promiseBuffer": []
        }
    """
    And  meta data /account/Euro/meta should be
    """
        {
            "accountName": "Euro",
            "isBalanceCheck": false,
            "currency": "EUR"
        }
    """

    When  active XRP account Ripple is created
    Then  snapshot /account/Ripple/snapshot/0000000000 should be
    """
        {
            "version": 0,
            "balance": 0,
            "promised": 0,
            "promiseBuffer": []
        }
    """
    And  meta data /account/Ripple/meta should be
    """
        {
            "accountName": "Ripple",
            "isBalanceCheck": true,
            "currency": "XRP"
        }
    """

  Scenario: Creating of transaction comitted
    When  pasive XXX account A is created
    And   active XXX account B is created
    And   123456789123313.000422901124 XXX is transfered from A to B with id xxx

    Then  transaction /transaction/xxx should be
    """
        [
            {
                "accountFrom": "A",
                "accountTo": "B",
                "amount": "123456789123313.000422901124",
                "currency": "XXX"
            }
        ]
    """
    And   transaction state /transaction_state/xxx should be
    """
        committed
    """
    And directory /account/A/events/0000000000 should contain 2 files
    And file /account/A/events/0000000000/0_-123456789123313.000422901124_xxx should exist
    And file /account/A/events/0000000000/1_-123456789123313.000422901124_xxx should exist
    And directory /account/B/events/0000000000 should contain 2 files
    And file /account/B/events/0000000000/0_123456789123313.000422901124_xxx should exist
    And file /account/B/events/0000000000/1_123456789123313.000422901124_xxx should exist

  Scenario: Creating of transaction rejected (insufficient funds)
    When  pasive XXX account C is created
    And   active XXX account D is created
    And   123456789123313.000422901124 XXX is transfered from D to C with id yyy

    Then  transaction /transaction/yyy should be
    """
        [
            {
                "accountFrom": "D",
                "accountTo": "C",
                "amount": "123456789123313.000422901124",
                "currency": "XXX"
            }
        ]
    """
    And   transaction state /transaction_state/yyy should be
    """
        rollbacked
    """
    And directory /account/C/events/0000000000 should contain 2 files
    And file /account/C/events/0000000000/0_123456789123313.000422901124_yyy should exist
    And file /account/C/events/0000000000/2_123456789123313.000422901124_yyy should exist
    And directory /account/D/events/0000000000 should contain 0 files
