require_relative 'rest_service'

class WallAPI
  include RESTServiceHelper

  attr_reader :base_url

  def initialize()
    @base_url = "http://wall:8080" # fixme discover
  end

  def create_account(tenant_id, account_name, currency, activity)
    body = {
      accountNumber: account_name,
      currency: currency,
      isBalanceCheck: activity
    }
    post("#{base_url}/v1/sparrow/account/#{tenant_id}", body)
  end

  def get_balance(tenant_id, account_name)
    get("#{base_url}/v1/sparrow/account/#{tenant_id}/#{account_name}")
  end

  def single_transfer(tenant_id, from, to, amount, currency, id = nil)
    body = {
      transfers: [{
        credit: to,
        debit: from,
        amount: amount,
        currency: currency
      }]
    }

    body["id"] = id unless id.nil?
    post("#{base_url}/v1/sparrow/transaction/#{tenant_id}", body)
  end

  def multi_transfer(tenant_id, transaction_id, transfers)
    body = {
      id: transaction_id,
      transfers: transfers
    }
    post("#{base_url}/v1/sparrow/transaction/#{tenant_id}", body)
  end

  def forward_transfer(tenant_id, transaction_id, transfer_id, side, account)
    body = {
      tenant: tenant_id,
      side: side,
      targetAccount: account
    }
    patch("#{base_url}/v1/sparrow/transaction/#{tenant_id}/#{transaction_id}/#{transfer_id}", body)
  end

  def health_check()
    get("#{base_url}/health")
  end

end
