Feature: Search API test

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
        Accounts(tenant: "SEARCH") {
          name
          currency
        }
      }
    """
    Then GraphQL responsed with
    """
      {
        "data": {
          "Accounts": [
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
      fragment accountFields on Account {
        name
        isBalanceCheck
        currency
      }

      fragment transferFields on Transfer {
        amount
        currency
        credit {
          ...accountFields
        }
        debit {
          ...accountFields
        }
      }

      fragment transactionFields on Transaction {
        status
        transfers {
          ...transferFields
        }
      }

      query {
        Transfers(tenant: "SEARCH") {
          ...transferFields
        }

        Transactions(tenant: "SEARCH") {
          ...transactionFields
        }
      }
    """
    Then GraphQL responsed with
    """
      {
        "data": {
          "Transactions": [
            {
              "status": "committed",
              "transfers": [
                {
                  "credit": {
                    "isBalanceCheck": true,
                    "name": "Credit"
                  },
                  "debit": {
                    "isBalanceCheck": false,
                    "name": "Debit"
                  },
                  "amount": "1",
                  "currency": "EUR"
                }
              ]
            }
          ]
        }
      }
    """
