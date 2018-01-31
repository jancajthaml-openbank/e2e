Feature: Journal integrity test

  Background: Basic orchestration

    Given container wall should be running
    And   container lake should be running
    And   container vault should be running
    And   wall is listening on 8080
    And   wall is healthy

  Scenario: Creation of account
    Given tenant is test

    When  pasive EUR account A is created
    Then  snapshot /account/A/snapshot/0000000000 should be
    """
        {
            "version": 0,
            "balance": 0,
            "promised": 0,
            "promiseBuffer": []
        }
    """
    And  meta data /account/A/meta should be
    """
        {
            "accountName": "A",
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

