Feature: Metrics test

  Scenario: metrics have expected keys
    Given appliance is running
    And   vault METRICS is onbdoarded
    And   ledger METRICS is onbdoarded

    Then metrics file /opt/ledger/metrics/metrics.METRICS.json should have following keys:
    """
      promisedTransactions
      promisedTransfers
      committedTransactions
      committedTransfers
      rollbackedTransactions
      rollbackedTransfers
      forwardedTransactions
      forwardedTransfers
    """
    And metrics file /opt/ledger/metrics/metrics.json should have following keys:
    """
      createTransactionLatency
      forwardTransferLatency
      getTransactionLatency
      getTransactionsLatency
    """
