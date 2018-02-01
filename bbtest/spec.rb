require 'turnip/rspec'
require 'json'
require 'thread'

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

class Hash

  def deep_diff(b)
    a = self
    (a.keys | b.keys).each_with_object({}) do |k, diff|
      if a[k] != b[k]
        if a[k].respond_to?(:deep_diff) && b[k].respond_to?(:deep_diff)
          diff[k] = a[k].deep_diff(b[k])
        else
          diff[k] = [a[k], b[k]]
        end
      end
    end
  end

end

module Enumerable

  def in_parallel_n(n)
    todo = Queue.new
    ts = (1..n).map{
      Thread.new{
        while x = todo.deq
          yield(x[0])
        end
      }
    }
    each{|x| todo << [x]}
    n.times{ todo << nil }
    ts.each{|t| t.join}
  end

end
