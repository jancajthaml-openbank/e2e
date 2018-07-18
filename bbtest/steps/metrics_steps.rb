require_relative 'placeholders'

require 'json'

step "metrics should report :count created accounts" do |count|
  abspath = "/metrics/e2e_vault_#{$tenant_id}_metrics.json"

  eventually(timeout: 3) {
    unless File.file?(abspath)
      raise "file:  #{abspath} is a directory" if File.directory?(abspath)
      raise "file:  #{abspath} was not found\nfiles: #{Dir[File.dirname(abspath)+"/*"]}"
    end

    contents = File.open(abspath, 'r') { |f|
      JSON.parse(f.read())
    }

    expect(contents["createdAccounts"]).to eq(count), "in #{contents}"
  }
end

step "metrics events should cancel out" do ||
  abspath = "/metrics/e2e_vault_#{$tenant_id}_metrics.json"

  eventually(timeout: 3) {
    unless File.file?(abspath)
      raise "file:  #{abspath} is a directory" if File.directory?(abspath)
      raise "file:  #{abspath} was not found\nfiles: #{Dir[File.dirname(abspath)+"/*"]}"
    end

    contents = File.open(abspath, 'r') { |f|
      JSON.parse(f.read())
    }

    raise "no promises in #{contents}" unless contents["promisesAccepted"] > 0

    initials = contents["promisesAccepted"]
    terminals = contents["commitsAccepted"] + contents["rollbacksAccepted"]

    expect(initials - terminals).to eq(0), "in #{contents}"
  }
end
