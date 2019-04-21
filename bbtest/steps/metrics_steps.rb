require_relative 'placeholders'

require 'json'

step "metrics for tenant :tenant should report :count created accounts" do |tenant, count|
  eventually(timeout: 3) {
    metrics = $appliance.get_metrics("vault", "metrics.#{tenant}.json")
    expect(metrics["createdAccounts"]).to eq(count)
  }
end

step "metrics should report :count created transfers" do |count|
  eventually(timeout: 3) {
    createdTransfers = $appliance.get_wall_instances().reduce(0) { |sum, wall|
      sum + $appliance.get_metrics("wall", "wall")["createdTransfers"].to_i
    }
    expect(createdTransfers).to eq(count)
  }
end

step "metrics events for tenant :tenant should cancel out" do |tenant|
  eventually(timeout: 3) {
    metrics = $appliance.get_metrics("vault", "metrics.#{tenant}.json")

    raise "no promises in #{contents}" unless metrics["promisesAccepted"] > 0

    initials = metrics["promisesAccepted"]
    terminals = metrics["commitsAccepted"] + metrics["rollbacksAccepted"]

    expect(initials - terminals).to eq(0), "promises and terminals don't cancel out in: #{contents}"
  }
end

step "metrics file :filename should have following keys:" do |path, keys|
  expected_keys = keys.split("\n").map(&:strip).reject { |x| x.empty? }

  eventually(timeout: 3) {
    expect(File.file?(path)).to be(true)
  }

  metrics_keys = File.open(path, 'rb') { |f| JSON.parse(f.read).keys }

  expect(metrics_keys).to match_array(expected_keys)
end
