require 'turnip/rspec'
require 'json'
require 'thread'
require_relative 'pimp'

Thread.abort_on_exception = true

RSpec.configure do |config|
  config.raise_error_for_unimplemented_steps = true
  config.color = true

  Dir.glob("./helpers/*_helper.rb") { |f| load f }
  config.include EventuallyHelper, :type => :feature
  Dir.glob("./steps/*_steps.rb") { |f| load f, true }

  config.before(:suite) do |_suite|
    puts "[info] before suite start"

    ["/data", "/logs"].par { |folder|
      FileUtils.rm_rf Dir.glob("#{folder}/*")
    }

    $http_client = HTTPClient.new()

    puts "[info] before suite done"
  end

  config.after(:suite) do |_suite|
    puts ""
    puts "[info] after suite start"

    get_containers = -> (image) {
      containers = %x(docker ps -aqf "ancestor=#{image}" 2>/dev/null)
      return ($? == 0 ? containers.split("\n") : [])
    }

    teardown_container = -> (container) {
      label = %x(docker inspect --format='{{.Name}}' #{container})
      label = ($? == 0 ? label.strip : container)

      %x(docker logs #{container} >/logs/#{label}.log 2>&1)
      %x(docker kill --signal="TERM" #{container} &>/dev/null || :)
      %x(docker rm -f #{container} &>/dev/null || :)
    }

    (
      get_containers.call("openbank/wall") <<
      get_containers.call("openbank/vault") <<
      get_containers.call("openbank/lake")
    ).flatten.par { |container| teardown_container.call(container) }

    FileUtils.rm_rf Dir.glob("/data/*")

    print "[info] after suite done"
  end

end
