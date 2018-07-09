require_relative 'rest_service'

class WallAPI
  include RESTServiceHelper

  attr_reader :public_uri, :private_uri

  def initialize()
    @public_uri = "http://wall:8080"
    @private_uri = "http://wall:8888"
  end

  ######################################################### account methods ####

  def create_account(tenant_id, account_name, currency, activity)
    body = {
      accountNumber: account_name,
      currency: currency,
      isBalanceCheck: activity
    }
    post("#{public_uri}/account/#{tenant_id}", body)
  end

  def get_balance(tenant_id, account_name)
    get("#{public_uri}/account/#{tenant_id}/#{account_name}")
  end

  ##################################################### transaction methods ####

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
    post("#{public_uri}/transaction/#{tenant_id}", body)
  end

  def multi_transfer(tenant_id, transaction_id, transfers)
    body = {
      id: transaction_id,
      transfers: transfers
    }
    post("#{public_uri}/transaction/#{tenant_id}", body)
  end

  def forward_transfer(tenant_id, transaction_id, transfer_id, side, account)
    body = {
      tenant: tenant_id,
      side: side,
      targetAccount: account
    }
    patch("#{public_uri}/transaction/#{tenant_id}/#{transaction_id}/#{transfer_id}", body)
  end

  def health_check()
    get("#{private_uri}/health")
  end

end
