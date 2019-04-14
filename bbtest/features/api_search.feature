Feature: Search API test

  Scenario: setup
    Given appliance is running
    And   vault SEARCH is onbdoarded
    And   ledger SEARCH is onbdoarded

  Scenario: Accounts query
    When  active EUR account SEARCH/ReplayCredit is created
    And   pasive EUR account SEARCH/ReplayDebit is created

    When  I request search
    """
      query {
        Accounts(tenant: "SEARCH") {
          name
          currency
        }
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
    And   1 EUR is transferred from SEARCH/Debit to SEARCH/Credit

    When  I request search
    """
      fragment accountFields on Account {
        name
        isBalanceCheck
        currency
      }

      query {
        Transactions(tenant: "SEARCH") {
          status
          transfers {
            credit {
              ...accountFields
            }
            debit {
              ...accountFields
            }
            amount
            currency
          }
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
