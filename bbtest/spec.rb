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

    FileUtils.rm_rf Dir.glob("/data/*")
    FileUtils.rm_rf Dir.glob("/logs/*")

    $http_client = HTTPClient.new()

    puts "[info] before suite done"
  end

  config.after(:suite) do |_suite|
    puts ""
    puts "[info] after suite start"

    teardown_vaults = Proc.new {
      # fixme each of vaults in parallel
      vaults = %x(docker ps -aqf "ancestor=openbank/vault" 2>/dev/null)
      vaults.split("\n").each { |container|

        label = %x(docker inspect --format='{{.Name}}' #{container})
        label = $? == 0 ? label.strip : container

        %x(docker logs #{container} >/logs/#{label}.log 2>&1 )

        %x(docker kill --signal="TERM" #{container} &>/dev/null || :)
        %x(docker rm -f #{container} &>/dev/null || :)
      } if $? == 0
    }

    teardown_walls = Proc.new {
      # fixme each of wall in parallel
      walls = %x(docker ps -aqf "ancestor=openbank/wall" 2>/dev/null)
      walls.split("\n").each { |container|

        label = %x(docker inspect --format='{{.Name}}' #{container})
        label = $? == 0 ? label.strip : container

        %x(docker logs #{container} >/logs/#{label}.log 2>&1 )

        %x(docker kill --signal="TERM" #{container} &>/dev/null || :)
        %x(docker rm -f #{container} &>/dev/null || :)
      } if $? == 0
    }

    teardown_lakes = Proc.new {
      # fixme each of lake in parallel
      lakes = %x(docker ps -aqf "ancestor=openbank/lake" 2>/dev/null)
      lakes.split("\n").each { |container|

        label = %x(docker inspect --format='{{.Name}}' #{container})
        label = $? == 0 ? label.strip : container

        %x(docker logs #{container} >/logs/#{label}.log 2>&1 )

        %x(docker kill --signal="TERM" #{container} &>/dev/null || :)
        %x(docker rm -f #{container} &>/dev/null || :)
      } if $? == 0
    }

    [teardown_vaults, teardown_walls, teardown_lakes].in_parallel_n(3){ |f| f.call }

    print "[info] after suite done"
  end

end
