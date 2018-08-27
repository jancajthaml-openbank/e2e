require_relative 'placeholders'

require 'json'

step "metrics for tenant :tenant should report :count created accounts" do |tenant, count|
  metrics = $appliance.get_metrics("vault@#{tenant}")
  expect(metrics["createdAccounts"]).to eq(count)
end

step "metrics should report :count created transfers" do |count|
  eventually(timeout: 3) {
    createdTransfers = $appliance.get_wall_instances().reduce(0) { |sum, wall|
      sum + $appliance.get_metrics(wall)["createdTransfers"].to_i
    }

    expect(createdTransfers).to eq(count)
  }
end

step "metrics events for tenant :tenant should cancel out" do |tenant|
  metrics = $appliance.get_metrics("vault@#{tenant}")

  raise "no promises in #{contents}" unless metrics["promisesAccepted"] > 0

  initials = metrics["promisesAccepted"]
  terminals = metrics["commitsAccepted"] + metrics["rollbacksAccepted"]

  expect(initials - terminals).to eq(0), "promises and terminals don't cancel out in: #{contents}"
end
