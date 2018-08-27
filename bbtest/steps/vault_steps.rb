require_relative 'placeholders'

require 'json'
require 'bigdecimal'

step ":activity :currency account :account is created" do |activity, currency, account|
  (tenant, account) = account.split('/')

  body = {
    accountNumber: account,
    currency: currency,
    isBalanceCheck: activity
  }.to_json

  cmd = [
    "curl --insecure",
    "-X POST",
    "https://127.0.0.1/account/#{tenant} -sw \"%{http_code}\"",
    "-d \'#{body}\'",
  ].join(" ")

  resp = nil

  eventually() {
    resp = %x(#{cmd})
    expect($?).to be_success, resp
  }

  code = resp[resp.length-3...resp.length].to_i
  expect(code).to satisfy { |x| x == 200 || x == 409 }
end

step ":account balance should be :amount :currency" do |account, amount, currency|
  (tenant, account) = account.split('/')

  cmd = [
    "curl --insecure",
    "https://127.0.0.1/account/#{tenant}/#{account} -sw \"%{http_code}\"",
  ].join(" ")

  response = Hash.new
  resp = nil

  resp = %x(#{cmd})
  response[:code] = resp[resp.length-3...resp.length].to_i
  response[:body] = resp[0...resp.length-3] unless resp.nil?

  expect(response[:code]).to eq(200)

  body = JSON.parse(response[:body])

  expect(body["currency"]).to eq(currency)
  expect(BigDecimal.new(body["balance"]).to_s('F')).to eq(BigDecimal.new(amount).to_s('F'))
end

step ":account should exist" do |account|
  (tenant, account) = account.split('/')

  cmd = [
    "curl --insecure",
    "https://127.0.0.1/account/#{tenant}/#{account} -sw \"%{http_code}\"",
  ].join(" ")

  resp = %x(#{cmd})
  code = resp[resp.length-3...resp.length].to_i

  expect(code).to eq(200)
end

step ":account should not exist" do |account|
  (tenant, account) = account.split('/')

  cmd = [
    "curl --insecure",
    "https://127.0.0.1/account/#{tenant}/#{account} -sw \"%{http_code}\"",
  ].join(" ")

  resp = %x(#{cmd})
  code = resp[resp.length-3...resp.length].to_i

  expect(code).to eq(404)

end
