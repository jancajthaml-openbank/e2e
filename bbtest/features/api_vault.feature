Feature: Vault API test

  Scenario: vault setup
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


  Scenario: Account API  - valid replay, invalid replay
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
        "isBalanceCheck": true
      }
      """
    Then HTTP response is
      | key    | value |
      | status | 409   |

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
        "format": "bbtest",
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
        "format": "bbtest",
        "balance": "0.0",
        "blocking": "0.0",
        "isBalanceCheck": false
      }
      """
