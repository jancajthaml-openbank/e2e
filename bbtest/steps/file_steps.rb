step "file :path should exist" do |path|
  expect(File.file?("/data/#{@tenant_id}#{path}")).to be_truthy
end

# input matching
placeholder :path do
  match(/((?:\/[a-z0-9]+[a-z0-9(\/)(\-)]{1,100}[\w,\s-]+\.?[A-Za-z]{0,20})+)/) do |path|
    path
  end
end
