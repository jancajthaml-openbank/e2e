require_relative 'placeholders'

require 'json'

step "metrics should report :count created accounts" do |count|
  abspath = "/opt/metrics/metrics_bbtest_vault_#{@tenant_id}.json"
  unless File.file?(abspath)
    raise "file:  #{abspath} is a directory" if File.directory?(abspath)
    raise "file:  #{abspath} was not found\nfiles: #{Dir[File.dirname(abspath)+"/*"]}"
  end

  eventually(timeout: 3) {
    contents = JSON.parse(File.open(abspath, 'r').read)
    expect(contents["ACCOUNTS-CREATED"]).to eq(count)
  }
end

step "metrics events should cancel out" do ||
  abspath = "/opt/metrics/metrics_bbtest_vault_#{@tenant_id}.json"
  unless File.file?(abspath)
    raise "file:  #{abspath} is a directory" if File.directory?(abspath)
    raise "file:  #{abspath} was not found\nfiles: #{Dir[File.dirname(abspath)+"/*"]}"
  end

  eventually(timeout: 3) {
    contents = JSON.parse(File.open(abspath, 'r').read)
    raise "no promises" unless contents["PROMISES-ACCEPTED"] > 0

    initials = contents["PROMISES-ACCEPTED"]
    terminals = contents["COMMITS-ACCEPTED"] + contents["ROLLBACKS-ACCEPTED"]

    expect(initials - terminals).to eq(0)
  }
end
