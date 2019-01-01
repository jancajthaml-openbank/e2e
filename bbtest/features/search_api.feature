Feature: Search API test

  Scenario: setup
    Given appliance is running
    And   vault SEARCH is onbdoarded

  Scenario: Accounts query
    When  active EUR account SEARCH/ReplayCredit is created
    And   pasive EUR account SEARCH/ReplayDebit is created

    When  I request search
    """
      Accounts(tenant: "SEARCH") {
        name
        currency
      }
    """
    Then  search responds with 200
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
    And   1 EUR is transfered from Debit to Credit for tenant SEARCH

    When  I request search
    """
      Transactions(tenant: "SEARCH") {
        status
        transfers {
          credit {
            name
            isBalanceCheck
          }
          debit {
            name
            isBalanceCheck
          }
          amount
          currency
        }
      }
    """
    Then  search responds with 200
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
