Feature: Journal integrity test

  Background: Basic orchestration

    Given container wall should be running
    And   container lake should be running
    And   container vault should be running
    And   wall is listening on 8080
    And   wall is healthy

  Scenario: Creation of account
    Given tenant is test

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

  Scenario: Creating of transaction
    Given tenant is test

    When  pasive XXX account A is created
    And   active XXX account B is created
    And   123456789123313.000422901124 XXX is transfered from A to B with id xxx

    Then  file /transaction/xxx should exist
    And   file /transaction_state/xxx should exist

