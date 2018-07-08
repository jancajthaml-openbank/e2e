require_relative 'placeholders'
require 'json'
require 'bigdecimal'

step ":activity :currency account :account is created" do |activity, currency, account|
  resp = HttpClient.wall.create_account($tenant_id, account, currency, activity)
  expect(resp.status).to satisfy { |code| code == 200 || code == 409 }
end

step ":account should exist" do |account|
  resp = HttpClient.wall.get_balance($tenant_id, account)
  expect(resp.status).to satisfy { |code| code == 200 || code == 409 }
end

step ":account should not exist" do |account|
  resp = HttpClient.wall.get_balance($tenant_id, account)
  expect(resp.status).to eq(404)
end

step ":account balance should be :amount :currency" do |account, amount, currency|
  resp = HttpClient.wall.get_balance($tenant_id, account)
  expect(resp.status).to eq(200)

  body = JSON.parse(resp.body)

  expect(body["currency"]).to eq(currency)
  expect(BigDecimal.new(body["balance"]).to_s('F')).to eq(BigDecimal.new(amount).to_s('F'))
end

step ":amount :currency is transfered from :from to :to" do |amount, currency, from, to|
  resp = HttpClient.wall.single_transfer($tenant_id, from, to, amount, currency)
  raise "failed to create transaction with #{resp.status}" unless resp.status == 200 || resp.status == 201

  begin
    resp_body = JSON.parse(resp.body)
    @transaction = resp_body["transaction"]
    @transfers = resp_body["transfers"]
  rescue JSON::ParserError
    raise "invalid response got \"#{resp.body.strip}\""
  end
end

step ":amount :currency is transfered from :from to :to with id :id" do |amount, currency, from, to, id|
  resp = HttpClient.wall.single_transfer($tenant_id, from, to, amount, currency, id)
  raise "failed to create transaction with #{resp.status}" unless resp.status == 200 || resp.status == 201

  begin
    resp_body = JSON.parse(resp.body)
    @transaction = resp_body["transaction"]
    @transfers = resp_body["transfers"]
  rescue JSON::ParserError
    raise "invalid response got \"#{resp.body.strip}\""
  end
end

step "Following transaction :transaction_id is created :count times" do |transaction_id, count, data = nil|
  transfers = []

  data.each_line.each { |transfer|
    parts = transfer.split(" ")

    transfers << {
      id: parts[4],
      credit: parts[1],
      debit: parts[0],
      amount: parts[2],
      currency: parts[3]
    }
  }

  responses = []
  wait_until = Time.now + 10

  [*1..count].each { |_|
    begin
      resp = HttpClient.wall.multi_transfer($tenant_id, transaction_id, transfers)
      raise if resp.status == 503
      responses << resp.status
    rescue Exception => e
      raise e if Time.now >= wait_until
      retry
    end
  }

  responses.each { |status| expect(status).to eq(200) }
end

step ":transaction_id :transfer_id :side side is forwarded to :account" do |transaction_id, transfer_id, side, account|
  resp = HttpClient.wall.forward_transfer($tenant_id, transaction_id, transfer_id, side, account)
  expect(resp.status).to eq(200)
end

