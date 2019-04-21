
step "appliance is running" do ||
  eventually() {
    expect($appliance.ready?).to be(true)
  }
end

step "vault :tenant is onbdoarded" do |tenant|
  uri = "https://127.0.0.1:4400/tenant/#{tenant}"

  send "I request curl :http_method :url", "POST", uri
  send "curl responds with :http_status", 200

  $appliance.update_units()

  send "appliance is running"
end

step "ledger :tenant is onbdoarded" do |tenant|
  uri = "https://127.0.0.1:4401/tenant/#{tenant}"

  send "I request curl :http_method :url", "POST", uri
  send "curl responds with :http_status", 200

  $appliance.update_units()

  send "appliance is running"
end
