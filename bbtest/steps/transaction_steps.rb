require_relative 'placeholders'

require 'json'
require 'bigdecimal'

step "following transaction is created for tenant :tenant" do |tenant, data = nil|
  body = JSON.parse(data).to_json

  cmd = [
    "curl --insecure",
    "-X POST",
    "https://127.0.0.1/transaction/#{tenant} -sw \"%{http_code}\"",
    "-d \'#{body}\'",
  ].join(" ")

  resp = %x(#{cmd})
  code = resp[resp.length-3...resp.length].to_i

  expect(code).to satisfy { |x| x == 200 || x == 201 }
end

step "following transaction is created :count times for tenant :tenant" do |count, tenant, data = nil|
  body = JSON.parse(data).to_json

  cmd = [
    "curl --insecure",
    "-X POST",
    "https://127.0.0.1/transaction/#{tenant} -sw \"%{http_code}\"",
    "-d \'#{body}\'",
  ].join(" ")

  responses = []

  [*1..count].each { |_|
    eventually() {
      resp = %x(#{cmd})
      code = resp[resp.length-3...resp.length].to_i
      expect(code).not_to eq(504)
      responses << code
    }
  }

  responses.each { |status| expect(status).to eq(200) }
end

step ":transaction_id :transfer_id :side side is forwarded to :acc for tenant :tenant" do |transaction_id, transfer_id, side, acc, tenant|
  body = {
    tenant: tenant,
    side: side,
    targetAccount: acc
  }.to_json

  cmd = [
    "curl --insecure",
    "-X PATCH",
    "https://127.0.0.1/transaction/#{tenant}/#{transaction_id}/#{transfer_id} -sw \"%{http_code}\"",
    "-d \'#{body}\'",
  ].join(" ")

  resp = %x(#{cmd})
  code = resp[resp.length-3...resp.length].to_i
  expect(code).to satisfy { |x| x == 200 || x == 201 }
end

step ":amount :currency is transfered from :from to :to for tenant :tenant" do |amount, currency, from, to, tenant|
  body = {
    transfers: [{
      credit: to,
      debit: from,
      amount: amount,
      currency: currency
    }]
  }.to_json

  cmd = [
    "curl --insecure",
    "-X POST",
    "https://127.0.0.1/transaction/#{tenant} -sw \"%{http_code}\"",
    "-d \'#{body}\'",
  ].join(" ")

  resp = %x(#{cmd})
  code = resp[resp.length-3...resp.length].to_i
  expect(code).to satisfy { |x| x == 200 || x == 201 }
end
