
step "appliance is running" do ||
  eventually() {
    expect($appliance.ready?).to be(true)
  }
end

step "vault :tenant is onbdoarded" do |tenant|
  send "I request curl :http_method :url", "POST", "https://127.0.0.1:4400/tenant/#{tenant}"

  resp = %x(#{@http_req})
  code = resp[resp.length-3...resp.length].to_i

  expect(code).to eq(200)

  $appliance.update_units()

  eventually() {
    expect($appliance.ready?).to be(true)
  }
end
