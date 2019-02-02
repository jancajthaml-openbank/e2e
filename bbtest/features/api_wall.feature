Feature: Wall API test

  Scenario: setup
    Given appliance is running
    And   vault APITRN is onbdoarded
    And   pasive XXX account APITRN/xxx is created
    And   pasive XXX account APITRN/yyy is created

  Scenario: Transaction API - invalid transaction side
    When  I request curl POST https://127.0.0.1/transaction/APITRN
    """
      {
        "transfers": [
          {
            "credit": "Credit",
            "debit": "Debit",
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
    When  I request curl POST https://127.0.0.1/transaction/APITRN
    """
      {
        "transfers": [
          {
            "credit": "xxx",
            "debit": "yyy",
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
    When  I request curl GET https://127.0.0.1/transaction/APITRN/unique_transaction_id
    Then  curl responds with 404
    """
      {}
    """

    When  I request curl POST https://127.0.0.1/transaction/APITRN
    """
      {
        "id": "unique_transaction_id",
        "transfers": [
          {
            "id": "unique_transfer_id",
            "valueDate": "2018-03-04T17:08:22Z",
            "credit": "xxx",
            "debit": "yyy",
            "amount": "1.0",
            "currency": "XXX"
          }
        ]
      }
    """
    Then  curl responds with 200
    """
      {
        "transaction": "unique_transaction_id",
        "transfers": [
          "unique_transfer_id"
        ]
      }
    """

    When  I request curl POST https://127.0.0.1/transaction/APITRN
    """
      {
        "id": "unique_transaction_id",
        "transfers": [
          {
            "id": "unique_transfer_id",
            "valueDate": "2018-03-04T17:08:22Z",
            "credit": "xxx",
            "debit": "yyy",
            "amount": "1.0",
            "currency": "XXX"
          }
        ]
      }
    """
    Then  curl responds with 200
    """
      {
        "transaction": "unique_transaction_id",
        "transfers": [
          "unique_transfer_id"
        ]
      }
    """

    When  I request curl GET https://127.0.0.1/transaction/APITRN/unique_transaction_id
    Then  curl responds with 200
    """
      {
        "id": "unique_transaction_id",
        "transfers": [
          {
            "id": "unique_transfer_id",
            "valueDate": "2018-03-04T17:08:22Z",
            "credit": "xxx",
            "debit": "yyy",
            "amount": "1.0",
            "currency": "XXX"
          }
        ]
      }
    """

    When  I request curl GET https://127.0.0.1/transaction/APITRN
    """
      {
        "id": "unique_transaction_id",
        "transfers": [
          {
            "id": "unique_transfer_id",
            "valueDate": "2018-03-04T17:08:22Z",
            "credit": "xxx",
            "debit": "yyy",
            "amount": "2.0",
            "currency": "XXX"
          }
        ]
      }
    """
    Then  curl responds with 409
    """
      {}
    """
