Feature: API test

  Background: Basic orchestration
    Given container wall should be running
    And   container lake should be running
    And   container vault should be running
    And   wall is listening on 8080
    And   wall is healthy
    And   storage is empty

  Scenario: Account API - account doesn't exist
    When  I call GET http://wall:8080/v1/sparrow/account/test/xxx
    Then  response status should be 404
    And   response content should be:
    """
        {}
    """

  Scenario: Account API - account created
    When  I call POST http://wall:8080/v1/sparrow/account/test
    """
        {
            "accountNumber": "xxx",
            "currency": "XXX",
            "isBalanceCheck": false
        }
    """
    Then  response status should be 200
    And   response content should be:
    """
        {}
    """

  Scenario: Account API - account already exists
    When  I call POST http://wall:8080/v1/sparrow/account/test
    """
        {
            "accountNumber": "yyy",
            "currency": "XXX",
            "isBalanceCheck": false
        }
    """
    Then  response status should be 200
    And   response content should be:
    """
        {}
    """

    When  I call POST http://wall:8080/v1/sparrow/account/test
    """
        {
            "accountNumber": "yyy",
            "currency": "XXX",
            "isBalanceCheck": false
        }
    """
    Then  response status should be 409
    And   response content should be:
    """
        {}
    """

  Scenario: Account API - get account balance
    When  I call GET http://wall:8080/v1/sparrow/account/test/xxx
    Then  response status should be 200
    And   response content should be:
    """
        {
            "currency": "XXX",
            "balance": "0"
        }
    """

  Scenario: Transaction API - invalid transaction side
    When  I call POST http://wall:8080/v1/sparrow/transaction/test
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
    Then  response status should be 417
    And   response content should be:
    """
        {}
    """

  Scenario: Transaction API - new transaction, valid resend, invalid resend
    When  I call POST http://wall:8080/v1/sparrow/transaction/test
    """
        {
            "id": "unique_transaction_id",
            "transfers": [{
                "id": "unique_transfer_id",
                "credit": "xxx",
                "debit": "yyy",
                "amount": "1.0",
                "currency": "XXX"
            }]
        }
    """
    Then  response status should be 200
    And   response content should be:
    """
        {
            "transaction": "unique_transaction_id",
            "transfers": [
                "unique_transfer_id"
            ]
        }
    """

    When  I call POST http://wall:8080/v1/sparrow/transaction/test
    """
        {
            "id": "unique_transaction_id",
            "transfers": [{
                "id": "unique_transfer_id",
                "credit": "xxx",
                "debit": "yyy",
                "amount": "1.0",
                "currency": "XXX"
            }]
        }
    """
    Then  response status should be 200
    And   response content should be:
    """
        {
            "transaction": "unique_transaction_id",
            "transfers": [
                "unique_transfer_id"
            ]
        }
    """

    When  I call POST http://wall:8080/v1/sparrow/transaction/test
    """
        {
            "id": "unique_transaction_id",
            "transfers": [{
                "id": "unique_transfer_id",
                "credit": "xxx",
                "debit": "yyy",
                "amount": "2.0",
                "currency": "XXX"
            }]
        }
    """
    Then  response status should be 409
    And   response content should be:
    """
        {}
    """
