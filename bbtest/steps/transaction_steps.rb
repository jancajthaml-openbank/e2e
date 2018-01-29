require 'json'
require 'bigdecimal'
require 'thread'  # for Mutex

step "tenant is :tenant" do |tenant|
  if tenant == "random"
    @tenant_id = (0...8).map { ('A'..'Z').to_a[rand(26)] }.join
  else
    @tenant_id = tenant
  end
end

step ":activity :currency account :account is created" do |activity, currency, account|
  resp = $http_client.wall_service.create_account(@tenant_id, account, currency, activity)
  expect(resp.status).to satisfy { |code| code == 200 || code == 409 }
end

step ":account should exist" do |account|
  resp = $http_client.wall_service.get_balance(@tenant_id, account)
  expect(resp.status).to satisfy { |code| code == 200 || code == 409 }
end

step ":account should not exist" do |account|
  resp = $http_client.wall_service.get_balance(@tenant_id, account)
  expect(resp.status).to eq(404)
end

step ":account balance should be :amount :currency" do |account, amount, currency|
  resp = $http_client.wall_service.get_balance(@tenant_id, account)
  expect(resp.status).to eq(200)

  body = JSON.parse(resp.body)

  expect(body["currency"]).to eq(currency)
  expect(BigDecimal.new(body["balance"]).to_s('F')).to eq(BigDecimal.new(amount).to_s('F'))
end

step ":amount :currency is transfered from :from to :to" do |amount, currency, from, to|
  resp = $http_client.wall_service.single_transfer(@tenant_id, from, to, amount, currency)
  expect(resp.status).to eq(200)

  begin
    resp_body = JSON.parse(resp.body)
    @transaction = resp_body["transaction"]
    @transfers = resp_body["transfers"]
  rescue JSON::ParserError
    raise "invalid response got \"#{resp.body.strip}\""
  end
end

step "Following transaction :transaction_id is created :times times" do |transaction_id, times, data = nil|
  transfers = []

  data.each_line do |transfer|
    parts = transfer.split(" ")

    transfers.push({
      id: parts[4],
      credit: parts[1],
      debit: parts[0],
      amount: parts[2],
      currency: parts[3]
    })
  end

  requests = [*1..times]
  responses = []
  mutex = Mutex.new

  32.times.map {
    Thread.new(requests, responses) do |requests, responses|
      while request = mutex.synchronize { requests.pop }
        mutex.synchronize { responses << $http_client.wall_service.multi_transfer(@tenant_id, transaction_id, transfers) }
      end
    end
  }.each(&:join)

  responses.each { |resp|
    expect(resp.status).to eq(200)
  }
end

step ":transaction_id :transfer_id :side side is forwarded to :account" do |transaction_id, transfer_id, side, account|
  resp = $http_client.wall_service.forward_transfer(@tenant_id, transaction_id, transfer_id, side, account)
  expect(resp.status).to eq(200)
end

# input matching
placeholder :activity do
  match(/(active|pasive)/) do |activity|
    activity == "active"
  end
end

placeholder :side do
  match(/(credit|debit)/) do |side|
    side
  end
end

placeholder :amount do
  match(/-?\d{1,100}\.\d{1,100}|-?\d{1,100}/) do |amount|
    amount
  end
end

placeholder :times do
  match(/\d{1,10}/) do |times|
    times.to_i
  end
end
