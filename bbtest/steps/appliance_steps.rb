
step "appliance is running" do ||
  eventually() {
    expect($appliance.ready?).to be(true)
  }
end

step "vault :tenant is onbdoarded" do |tenant|
  $appliance.onboard_vault(tenant)

  eventually() {
    expect($appliance.ready?).to be(true)
  }
end
