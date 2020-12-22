Feature: Vault API test

  Scenario: setup
    Given appliance is running
    And   vault APIACC is onboarded

  Scenario: Account API - account doesn't exist
    When I request HTTP https://127.0.0.1:4400/account/APIACC/xxx
      | key    | value |
      | method | GET   |
    Then HTTP response is
      | key    | value |
      | status | 404   |

  Scenario: Account API - account created
    When I request HTTP https://127.0.0.1:4400/account/APIACC
      | key    | value |
      | method | POST  |
      """
      {
        "name": "xxx",
        "format": "bbtest",
        "currency": "XXX",
        "isBalanceCheck": false
      }
      """
    Then HTTP response is
      | key    | value |
      | status | 200   |

  Scenario: Account API - request for account of non-existant vault
    When I request HTTP https://127.0.0.1:4400/account/nothing/xxx
      | key    | value |
      | method | GET   |
    Then HTTP response is
      | key    | value |
      | status | 504   |

  Scenario: Account API - account already exists
    When I request HTTP https://127.0.0.1:4400/account/APIACC
      | key    | value |
      | method | POST  |
      """
      {
        "name": "yyy",
        "format": "bbtest",
        "currency": "XXX",
        "isBalanceCheck": false
      }
      """
    Then HTTP response is
      | key    | value |
      | status | 200   |

    When I request HTTP https://127.0.0.1:4400/account/APIACC
      | key    | value |
      | method | POST  |
      """
      {
        "name": "yyy",
        "format": "bbtest",
        "currency": "XXX",
        "isBalanceCheck": false
      }
      """
    Then HTTP response is
      | key    | value |
      | status | 409   |

  Scenario: Account API - get account balance
    When I request HTTP https://127.0.0.1:4400/account/APIACC/xxx
      | key    | value |
      | method | GET   |
    Then HTTP response is
      | key    | value |
      | status | 200   |
      """
      {
        "currency": "XXX",
        "format": "BBTEST",
        "balance": "0.0",
        "blocking": "0.0",
        "isBalanceCheck": false
      }
      """

    When I request HTTP https://127.0.0.1:4400/account/APIACC/yyy
      | key    | value |
      | method | GET   |
    Then HTTP response is
      | key    | value |
      | status | 200   |
      """
      {
        "currency": "XXX",
        "format": "BBTEST",
        "balance": "0.0",
        "blocking": "0.0",
        "isBalanceCheck": false
      }
      """
