require_relative 'placeholders'

require 'json'
require 'bigdecimal'

step "following transaction is created for tenant :tenant" do |tenant, body = nil|
  send "I request curl :http_method :url", "POST", "https://127.0.0.1/transaction/#{tenant}", body

  resp = %x(#{@http_req})
  code = resp[resp.length-3...resp.length].to_i

  expect(code).to satisfy { |x| x == 200 || x == 201 }
end

step "following transaction is created :count times for tenant :tenant" do |count, tenant, body = nil|
  send "I request curl :http_method :url", "POST", "https://127.0.0.1/transaction/#{tenant}", body

  responses = []

  [*1..count].each { |_|
    eventually() {
      resp = %x(#{@http_req})
      code = resp[resp.length-3...resp.length].to_i
      expect(code).not_to eq(504)
      responses << code
    }
  }

  responses.each { |status| expect(status).to eq(200) }
end

step ":transaction_id :transfer_id :side side is forwarded to :acc for tenant :tenant" do |transaction_id, transfer_id, side, acc, tenant|
  send "I request curl :http_method :url", "PATCH", "https://127.0.0.1/transaction/#{tenant}/#{transaction_id}/#{transfer_id}", {
    tenant: tenant,
    side: side,
    targetAccount: acc
  }.to_json

  resp = %x(#{@http_req})
  code = resp[resp.length-3...resp.length].to_i

  expect(code).to satisfy { |x| x == 200 || x == 201 }
end

step ":amount :currency is transfered from :from to :to for tenant :tenant" do |amount, currency, from, to, tenant|
  send "I request curl :http_method :url", "POST", "https://127.0.0.1/transaction/#{tenant}", {
    transfers: [{
      credit: to,
      debit: from,
      amount: amount,
      currency: currency
    }]
  }.to_json

  resp = %x(#{@http_req})
  code = resp[resp.length-3...resp.length].to_i

  expect(code).to satisfy { |x| x == 200 || x == 201 }
end
