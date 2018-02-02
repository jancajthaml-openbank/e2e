require 'bigdecimal'
require 'json'
require 'date'

step "snapshot :path should be" do |path, expectation|
  abspath = "/data/#{@tenant_id}#{path}"
  raise "file:  #{abspath} was not found\nfiles: #{Dir[File.dirname(abspath)+"/*"]}" unless File.file?(abspath)

  contents = File.open(abspath, 'rb').read

  version = contents[0..4].unpack('L')[0]
  lines = contents[4..-1].split("\n").map(&:strip)

  balance = BigDecimal.new(lines[0]).to_s('F')
  promised = BigDecimal.new(lines[1]).to_s('F')
  buffer = lines[1..-2]

  expectation = JSON.parse(expectation)

  expected_version = expectation["version"].to_i
  expect(version).to eq(expected_version)

  expected_balance = BigDecimal.new(expectation["balance"]).to_s('F')
  expect(balance).to eq(expected_balance)

  expected_promised = BigDecimal.new(expectation["promised"]).to_s('F')
  expect(promised).to eq(expected_promised)

  # fixme validate in parallel
  expect(buffer).to match_array(expectation["promiseBuffer"])
end

step "meta data :path should be" do |path, expectation|
  abspath = "/data/#{@tenant_id}#{path}"
  raise "file:  #{abspath} was not found\nfiles: #{Dir[File.dirname(abspath)+"/*"]}" unless File.file?(abspath)

  contents = File.open(abspath, 'r').read
  balance_check = contents[0] != 'f'
  currency = contents[1..3]
  account_name = contents[4..-1]

  expectation = JSON.parse(expectation)

  expect(account_name).to eq(expectation["accountName"])
  expect(balance_check).to eq(expectation["isBalanceCheck"])
  expect(currency).to eq(expectation["currency"])
end

step "transaction :path should be" do |path, expectation|
  abspath = "/data/#{@tenant_id}#{path}"
  raise "file:  #{abspath} was not found\nfiles: #{Dir[File.dirname(abspath)+"/*"]}" unless File.file?(abspath)

  lines = File.open(abspath, 'r').read.split("\n")

  id = lines[0]
  now = DateTime.now

  # fixme validate in parallel
  transactions = lines[1..-1].map { |line|
    _, from, to, value_date, amount, currency = line.strip.split(" ")

    delta_seconds = ((now - Time.at(value_date.to_i).to_datetime) * 24 * 60 * 60).to_i
    raise "invalid valueDate" if delta_seconds > 60

    {
      "accountFrom" => from,
      "accountTo" => to,
      "amount" => BigDecimal.new(amount).to_s('F'),
      "currency" => currency
    }
  }

  expectation = JSON.parse(expectation)

  # fixme validate in parallel
  expect(transactions).to match_array(expectation)
end

step "transaction state :path should be" do |path, expectation|
  abspath = "/data/#{@tenant_id}#{path}"
  raise "file:  #{abspath} was not found\nfiles: #{Dir[File.dirname(abspath)+"/*"]}" unless File.file?(abspath)

  contents = File.open(abspath, 'r').read
  expect(contents).to eq(expectation.strip)
end

# input matching
placeholder :path do
  match(/((?:\/[a-z0-9]+[a-z0-9(\/)(\-)]{1,100}[\w,\s-]+\.?[A-Za-z0-9_-]{0,100})+)/) do |path|
    path
  end
end
