require_relative 'placeholders'

require 'json'
require 'bigdecimal'

step ":activity :currency account :account is created" do |activity, currency, account|
  (tenant, account) = account.split('/')

  send "I request curl :http_method :url", "POST", "https://127.0.0.1:4400/account/#{tenant}", {
    name: account,
    currency: currency,
    isBalanceCheck: activity
  }.to_json

  resp = nil
  eventually() {
    resp = %x(#{@http_req})
    expect($?).to be_success, resp
  }

  code = resp[resp.length-3...resp.length].to_i
  expect(code).to satisfy { |x| x == 200 || x == 409 }
end

step ":account balance should be :amount :currency" do |account, amount, currency|
  (tenant, account) = account.split('/')

  send "I request curl :http_method :url", "GET", "https://127.0.0.1:4400/account/#{tenant}/#{account}"

  response = Hash.new

  resp = %x(#{@http_req})
  response[:code] = resp[resp.length-3...resp.length].to_i
  response[:body] = resp[0...resp.length-3] unless resp.nil?

  expect(response[:code]).to eq(200)

  body = JSON.parse(response[:body])

  expect(body["currency"]).to eq(currency)
  expect(BigDecimal.new(body["balance"]).to_s('F')).to eq(BigDecimal.new(amount).to_s('F'))
end

step ":account should exist" do |account|
  (tenant, account) = account.split('/')

  send "I request curl :http_method :url", "GET", "https://127.0.0.1:4400/account/#{tenant}/#{account}"

  resp = %x(#{@http_req})
  code = resp[resp.length-3...resp.length].to_i

  expect(code).to eq(200)
end

step ":account should not exist" do |account|
  (tenant, account) = account.split('/')

  send "I request curl :http_method :url", "GET", "https://127.0.0.1:4400/account/#{tenant}/#{account}"

  resp = %x(#{@http_req})
  code = resp[resp.length-3...resp.length].to_i

  expect(code).to eq(404)
end
