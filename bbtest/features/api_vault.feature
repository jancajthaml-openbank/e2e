Feature: Vault API test

  Scenario: setup
    Given appliance is running
    And   vault APIACC is onbdoarded

  Scenario: Account API - account doesn't exist
    When  I request curl GET https://127.0.0.1:4400/account/APIACC/xxx
    Then  curl responds with 404
    """
      {}
    """

  Scenario: Account API - account created
    When  I request curl POST https://127.0.0.1:4400/account/APIACC
    """
      {
        "name": "xxx",
        "format": "bbtest",
        "currency": "XXX",
        "isBalanceCheck": false
      }
    """
    Then  curl responds with 200
    """
      {}
    """

  Scenario: Account API - request for account of non-existant vault
    When  I request curl GET https://127.0.0.1:4400/account/nothing/xxx
    Then  curl responds with 504
    """
      {}
    """

  Scenario: Account API - account already exists
    When  I request curl POST https://127.0.0.1:4400/account/APIACC
    """
      {
        "name": "yyy",
        "format": "bbtest",
        "currency": "XXX",
        "isBalanceCheck": false
      }
    """
    Then  curl responds with 200
    """
      {}
    """

    When  I request curl POST https://127.0.0.1:4400/account/APIACC
    """
      {
        "name": "yyy",
        "format": "bbtest",
        "currency": "XXX",
        "isBalanceCheck": false
      }
    """
    Then  curl responds with 409
    """
      {}
    """

  Scenario: Account API - get account balance
    When  I request curl GET https://127.0.0.1:4400/account/APIACC/xxx
    Then  curl responds with 200
    """
      {
        "currency": "XXX",
        "format": "BBTEST",
        "balance": "0",
        "blocking": "0",
        "isBalanceCheck": false
      }
    """

    When  I request curl GET https://127.0.0.1:4400/account/APIACC/yyy
    Then  curl responds with 200
    """
      {
        "currency": "XXX",
        "format": "BBTEST",
        "balance": "0",
        "blocking": "0",
        "isBalanceCheck": false
      }
    """
