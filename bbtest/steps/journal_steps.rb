require 'bigdecimal'
require 'json'

step "snapshot :path should be" do |path, expectation|
  abspath = "/data/#{@tenant_id}#{path}"

  unless File.file?(abspath)
    raise "file:  #{abspath} was not found\nfiles: #{Dir[File.dirname(abspath)+"/*"]}"
  end

  contents = File.open(abspath, 'rb').read

  version = contents[0..4].unpack('L')[0].to_i
  lines = contents[4..-1].split("\n").map { |line| line.strip }

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

  expect(buffer).to match_array(expectation["promiseBuffer"])
end

step "meta data :path should be" do |path, expectation|
  abspath = "/data/#{@tenant_id}#{path}"

  unless File.file?(abspath)
    raise "file:  #{abspath} was not found\nfiles: #{Dir[File.dirname(abspath)+"/*"]}"
  end

  contents = File.open(abspath, 'r').read
  balance_check = contents[0] != 'f'
  currency = contents[1..3]
  account_name = contents[4..-1]

  expectation = JSON.parse(expectation)

  expect(account_name).to eq(expectation["accountName"])
  expect(balance_check).to eq(expectation["isBalanceCheck"])
  expect(currency).to eq(expectation["currency"])

end

# input matching
placeholder :path do
  match(/((?:\/[a-z0-9]+[a-z0-9(\/)(\-)]{1,100}[\w,\s-]+\.?[A-Za-z]{0,20})+)/) do |path|
    path
  end
end
