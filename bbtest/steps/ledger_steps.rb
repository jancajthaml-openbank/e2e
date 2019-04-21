require_relative 'placeholders'

require 'json'
require 'bigdecimal'

step "following transaction is created from tenant :tenant" do |tenant, body = nil|
  send "following transaction is created :count times from tenant :tenant", 1, tenant, body
end

step "following transaction is created :count times from tenant :tenant" do |count, tenant, body = nil|
  uri = "https://127.0.0.1:4401/transaction/#{tenant}"

  send "I request curl :http_method :url", "POST", uri, body

  [*1..count].each { |_|
    eventually() {
      send "curl responds with :http_status", [200, 201]
    }
  }
end

step ":id :id :side side is forwarded to :account from tenant :tenant" do |transaction, transfer, side, account, tenant|
  (tenant, account) = account.split('/')

  payload = {
    side: side,
    target: {
      tenant: tenant,
      name: account
    }
  }.to_json

  uri = "https://127.0.0.1:4401/transaction/#{tenant}/#{transaction}/#{transfer}"

  send "I request curl :http_method :url", "PATCH", uri, payload
  send "curl responds with :http_status", [200, 201]
end

step ":amount :currency is transferred from :account to :account" do |amount, currency, from, to|
  (fromTenant, fromAccount) = from.split('/')
  (toTenant, toAccount) = to.split('/')

  payload = {
    transfers: [{
      credit: {
        name: toAccount,
        tenant: toTenant,
      },
      debit: {
        name: fromAccount,
        tenant: fromTenant,
      },
      amount: amount,
      currency: currency
    }]
  }.to_json

  send "following transaction is created from tenant :tenant", fromTenant, payload
end
