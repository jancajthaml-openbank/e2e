Feature: Data Warehouse API test

  Scenario: setup
    Given appliance is running
    And   vault SEARCH is onboarded
    And   ledger SEARCH is onboarded

  Scenario: Accounts query
    When  active EUR account SEARCH/ReplayCredit is created
    And   pasive EUR account SEARCH/ReplayDebit is created

    When  GraphQL requested with
    """
    query {
      accounts(tenant: "SEARCH", limit: 100, offset: 0) {
        name
        currency
      }
    }
    """
    Then GraphQL responsed with
    """
    {
      "data": {
        "accounts": [
          {
            "name": "ReplayCredit",
            "currency": "EUR"
          },
          {
            "name": "ReplayDebit",
            "currency": "EUR"
          }
        ]
      }
    }
    """

  Scenario: Transactions query
    When  active EUR account SEARCH/Credit is created
    And   pasive EUR account SEARCH/Debit is created
    And   1 EUR is transferred from SEARCH/Debit to SEARCH/Credit

    When  GraphQL requested with
    """
    fragment accountFields on account {
      name
    }

    fragment transferFields on transfer {
      amount
      currency
      credit {
        ...accountFields
      }
      debit {
        ...accountFields
      }
    }

    query {
      transfers(tenant: "SEARCH", limit: 100, offset: 0) {
        ...transferFields
      }
    }
    """
    Then GraphQL responsed with
    """
    {
      "data": {
        "transfers": [
          {
            "credit": {
              "name": "Credit"
            },
            "debit": {
              "name": "Debit"
            },
            "amount": 1,
            "currency": "EUR"
          }
        ]
      }
    }
    """
