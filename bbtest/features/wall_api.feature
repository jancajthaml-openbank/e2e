Feature: Wall API test

  Scenario: setup
    Given appliance is running
    And   vault WALL is onbdoarded

  Scenario: Account API - account doesn't exist
    When I request wall GET /account/WALL/xxx
    Then wall responds with 404
    """
      {}
    """

  Scenario: Account API - account created
    When I request wall POST /account/WALL
    """
      {
        "accountNumber": "xxx",
        "currency": "XXX",
        "isBalanceCheck": false
      }
    """
    Then wall responds with 200
    """
      {}
    """

  Scenario: Account API - account already exists
    When I request wall POST /account/WALL
    """
      {
        "accountNumber": "yyy",
        "currency": "XXX",
        "isBalanceCheck": false
      }
    """
    Then wall responds with 200
    """
      {}
    """

    When I request wall POST /account/WALL
    """
      {
        "accountNumber": "yyy",
        "currency": "XXX",
        "isBalanceCheck": false
      }
    """
    Then wall responds with 409
    """
      {}
    """

  Scenario: Account API - get account balance
    When I request wall GET /account/WALL/xxx
    Then wall responds with 200
    """
      {
        "currency": "XXX",
        "balance": "0",
        "blocking": "0",
        "isBalanceCheck": false
      }
    """

    When I request wall GET /account/WALL/yyy
    Then wall responds with 200
    """
      {
        "currency": "XXX",
        "balance": "0",
        "blocking": "0",
        "isBalanceCheck": false
      }
    """

  Scenario: Transaction API - invalid transaction side
    When I request wall POST /transaction/WALL
    """
      {
        "transfers": [{
          "credit": "Credit",
          "debit": "Debit",
          "amount": "1.0",
          "currency": "XXX"
        }]
      }
    """
    Then wall responds with 417
    """
      {}
    """

  Scenario: Transaction API - currency mismatch
    When I request wall POST /transaction/WALL
    """
      {
        "transfers": [{
          "credit": "xxx",
          "debit": "yyy",
          "amount": "1.0",
          "currency": "YYY"
        }]
      }
    """
    Then wall responds with 417
    """
      {}
    """

  Scenario: Transaction API - new transaction, valid resend, invalid resend
    When I request wall GET /transaction/WALL/unique_transaction_id
    Then wall responds with 404
    """
      {}
    """

    When I request wall POST /transaction/WALL
    """
      {
        "id": "unique_transaction_id",
        "transfers": [{
          "id": "unique_transfer_id",
          "valueDate": "2018-03-04T17:08:22Z",
          "credit": "xxx",
          "debit": "yyy",
          "amount": "1.0",
          "currency": "XXX"
        }]
      }
    """
    Then wall responds with 200
    """
      {
        "transaction": "unique_transaction_id",
        "transfers": [
          "unique_transfer_id"
        ]
      }
    """

    When I request wall POST /transaction/WALL
    """
      {
        "id": "unique_transaction_id",
        "transfers": [{
          "id": "unique_transfer_id",
          "valueDate": "2018-03-04T17:08:22Z",
          "credit": "xxx",
          "debit": "yyy",
          "amount": "1.0",
          "currency": "XXX"
        }]
      }
    """
    Then wall responds with 200
    """
      {
        "transaction": "unique_transaction_id",
        "transfers": [
          "unique_transfer_id"
        ]
      }
    """

    When I request wall GET /transaction/WALL/unique_transaction_id
    Then wall responds with 200
    """
      {
        "id": "unique_transaction_id",
        "transfers": [{
          "id": "unique_transfer_id",
          "valueDate": "2018-03-04T17:08:22Z",
          "credit": "xxx",
          "debit": "yyy",
          "amount": "1.0",
          "currency": "XXX"
        }]
      }
    """

    When I request wall GET /transaction/WALL
    """
      {
        "id": "unique_transaction_id",
        "transfers": [{
          "id": "unique_transfer_id",
          "valueDate": "2018-03-04T17:08:22Z",
          "credit": "xxx",
          "debit": "yyy",
          "amount": "2.0",
          "currency": "XXX"
        }]
      }
    """
    Then wall responds with 409
    """
      {}
    """
