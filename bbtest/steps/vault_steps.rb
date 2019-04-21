require_relative 'placeholders'

require 'json'
require 'bigdecimal'

step ":activity :currency account :account is created" do |activity, currency, account|
  (tenant, account) = account.split('/')

  uri = "https://127.0.0.1:4400/account/#{tenant}"

  payload = {
    name: account,
    currency: currency,
    isBalanceCheck: activity
  }.to_json

  send "I request curl :http_method :url", "POST", uri, payload
  send "curl responds with :http_status", [200, 409]
end

step ":account balance should be :amount :currency" do |account, amount, currency|
  (tenant, account) = account.split('/')

  uri = "https://127.0.0.1:4400/account/#{tenant}/#{account}"

  send "I request curl :http_method :url", "GET", uri
  send "curl responds with :http_status", 200

  body = JSON.parse(HTTPHelper.response[:body])

  expect(body["currency"]).to eq(currency)
  expect(BigDecimal.new(body["balance"]).to_s('F')).to eq(BigDecimal.new(amount).to_s('F'))
end

step ":account should exist" do |account|
  (tenant, account) = account.split('/')

  uri = "https://127.0.0.1:4400/account/#{tenant}/#{account}"

  send "I request curl :http_method :url", "GET", uri
  send "curl responds with :http_status", 200
end

step ":account should not exist" do |account|
  (tenant, account) = account.split('/')

  uri = "https://127.0.0.1:4400/account/#{tenant}/#{account}"

  send "I request curl :http_method :url", "GET", uri
  send "curl responds with :http_status", 404
end
