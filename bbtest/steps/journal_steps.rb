require_relative 'placeholders'

step "snapshot :account version :count should be" do |account, version, expectation|
  (tenant, account) = account.split('/')
  actual = Journal.account_snapshot(tenant, account, version)
  expectation = JSON.parse(expectation)

  expect(actual["version"]).to eq(expectation["version"])
  expect(actual["balance"]).to eq(expectation["balance"])
  expect(actual["promised"]).to eq(expectation["promised"])
  expect(actual["accountName"]).to eq(expectation["accountName"])
  expect(actual["isBalanceCheck"]).to eq(expectation["isBalanceCheck"])
  expect(actual["currency"]).to eq(expectation["currency"])
  expect(actual["promiseBuffer"]).to match_array(expectation["promiseBuffer"])
end

step "transaction :id of :tenant should be" do |id, tenant, expectation|
  transaction = Journal.transaction_data(tenant, id)
  expectation = JSON.parse(expectation)

  expect(transaction["id"]).to eq(expectation["id"]) unless expectation["id"].nil?

  expectation["transfers"].each { |e|
    found = false
    transaction["transfers"].each { |t|
      same = true
      same &&= t["id"] == e["id"] unless e["id"].nil?
      same &&= t["credit"] == e["credit"] unless e["credit"].nil?
      same &&= t["debit"] == e["debit"] unless e["debit"].nil?
      same &&= t["valueDate"] == e["valueDate"] unless e["valueDate"].nil?
      same &&= t["amount"] == e["amount"] unless e["amount"].nil?
      same &&= t["currency"] == e["currency"] unless e["currency"].nil?

      if same
        found = true
        break
      end
    }
    raise "#{e} not found in #{transaction}" unless found
  }
end

step "transaction :id state of :tenant should be :state" do |id, tenant, state|
  expect(Journal.transaction_state(tenant, id)).to eq(state)
end
