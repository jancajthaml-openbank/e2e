Feature: Ledger API test

  Scenario: setup
    Given appliance is running
    And   vault APITRN is onbdoarded
    And   ledger APITRN is onbdoarded
    And   pasive XXX account APITRN/xxx is created
    And   pasive XXX account APITRN/yyy is created

  Scenario: Transaction API - invalid transaction side
    When  I request curl POST https://127.0.0.1:4401/transaction/APITRN
    """
      {
        "transfers": [
          {
            "credit": {
              "tenant": "APITRN",
              "name": "Credit"
            },
            "debit": {
              "tenant": "APITRN",
              "name": "Debit"
            },
            "amount": "1.0",
            "currency": "XXX"
          }
        ]
      }
    """
    Then  curl responds with 417
    """
      {}
    """

  Scenario: Transaction API - currency mismatch
    When  I request curl POST https://127.0.0.1:4401/transaction/APITRN
    """
      {
        "transfers": [
          {
            "credit": {
              "tenant": "APITRN",
              "name": "xxx"
            },
            "debit": {
              "tenant": "APITRN",
              "name": "yyy"
            },
            "amount": "1.0",
            "currency": "YYY"
          }
        ]
      }
    """
    Then  curl responds with 417
    """
      {}
    """

  Scenario: Transaction API - new transaction, valid resend, invalid resend
    When  I request curl GET https://127.0.0.1:4401/transaction/APITRN/unique_transaction_id
    Then  curl responds with 404
    """
      {}
    """

    When  I request curl POST https://127.0.0.1:4401/transaction/APITRN
    """
      {
        "id": "unique_transaction_id",
        "transfers": [
          {
            "id": "unique_transfer_id",
            "valueDate": "2018-03-04T17:08:22Z",
            "credit": {
              "tenant": "APITRN",
              "name": "xxx"
            },
            "debit": {
              "tenant": "APITRN",
              "name": "yyy"
            },
            "amount": "1",
            "currency": "XXX"
          }
        ]
      }
    """
    Then  curl responds with 200
    """
      {
        "id": "unique_transaction_id",
        "transfers": [
          {
            "id": "unique_transfer_id",
            "valueDate": "2018-03-04T17:08:22Z",
            "credit": {
              "tenant": "APITRN",
              "name": "xxx"
            },
            "debit": {
              "tenant": "APITRN",
              "name": "yyy"
            },
            "amount": "1",
            "currency": "XXX"
          }
        ]
      }
    """

    When  I request curl POST https://127.0.0.1:4401/transaction/APITRN
    """
      {
        "id": "unique_transaction_id",
        "transfers": [
          {
            "id": "unique_transfer_id",
            "valueDate": "2018-03-04T17:08:22Z",
            "credit": {
              "tenant": "APITRN",
              "name": "xxx"
            },
            "debit": {
              "tenant": "APITRN",
              "name": "yyy"
            },
            "amount": "1",
            "currency": "XXX"
          }
        ]
      }
    """
    Then  curl responds with 200
    """
      {
        "id": "unique_transaction_id",
        "transfers": [
          {
            "id": "unique_transfer_id",
            "valueDate": "2018-03-04T17:08:22Z",
            "credit": {
              "tenant": "APITRN",
              "name": "xxx"
            },
            "debit": {
              "tenant": "APITRN",
              "name": "yyy"
            },
            "amount": "1",
            "currency": "XXX"
          }
        ]
      }
    """

    When  I request curl GET https://127.0.0.1:4401/transaction/APITRN/unique_transaction_id
    Then  curl responds with 200
    """
      {
        "id": "unique_transaction_id",
        "status": "committed",
        "transfers": [
          {
            "id": "unique_transfer_id",
            "valueDate": "2018-03-04T17:08:22Z",
            "credit": {
              "tenant": "APITRN",
              "name": "xxx"
            },
            "debit": {
              "tenant": "APITRN",
              "name": "yyy"
            },
            "amount": "1",
            "currency": "XXX"
          }
        ]
      }
    """

    When  I request curl GET https://127.0.0.1:4401/transaction/APITRN
    """
      {
        "id": "unique_transaction_id",
        "transfers": [
          {
            "id": "unique_transfer_id",
            "valueDate": "2018-03-04T17:08:22Z",
            "credit": {
              "tenant": "APITRN",
              "name": "xxx"
            },
            "debit": {
              "tenant": "APITRN",
              "name": "yyy"
            },
            "amount": "2",
            "currency": "XXX"
          }
        ]
      }
    """
    Then  curl responds with 409
    """
      {}
    """
