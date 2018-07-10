require 'turnip/rspec'
require 'json'
require 'thread'
require 'timeout'

Thread.abort_on_exception = true

RSpec.configure do |config|
  config.raise_error_for_unimplemented_steps = true
  config.color = true

  Dir.glob("./helpers/*_helper.rb") { |f| load f }
  config.include EventuallyHelper, :type => :feature
  config.include DeadlineHelper, :type => :feature
  Dir.glob("./steps/*_steps.rb") { |f| load f, true }

  config.before(:suite) do |_suite|
    print "[ suite starting ]\n"

    ZMQHelper.start()

    ["/data", "/metrics", "/reports"].each { |folder|
      FileUtils.mkdir_p folder
      FileUtils.rm_rf Dir.glob("#{folder}/*")
    }

    $tenant_id = nil

    print "[ suite started  ]\n"
  end

  config.after(:suite) do |_suite|
    print "\n[ suite ending   ]\n"

    get_containers = lambda do |image|
      containers = %x(docker ps -a --filter ancestor=#{image} --format "{{.ID}}")
      return ($? == 0 ? containers.split("\n") : [])
    end

    teardown_binary_container = lambda do |container|
      label = %x(docker inspect --format='{{.Name}}' #{container})
      label = ($? == 0 ? label.strip : container)

      %x(docker kill --signal="TERM" #{container} >/dev/null 2>&1 || :)
      %x(docker logs #{container} >/reports/#{label}.log 2>&1)
      %x(docker rm -f #{container} &>/dev/null || :)
    end

    teardown_service_container = lambda do |container|
      label = %x(docker inspect -f '{{.Name}}' #{container})
      label = ($? == 0 ? label.strip : container)

      %x(docker exec #{container} systemctl stop lake.service 2>&1)
      %x(docker exec #{container} journalctl -o short-precise -u lake.service --no-pager >/reports/#{label}.log 2>&1)
      %x(docker rm -f #{container} &>/dev/null || :)
    end

    begin
      Timeout.timeout(20) do
        (
          get_containers.call("openbank/wall") <<
          get_containers.call("openbank/search") <<
          get_containers.call("openbank/vault")
        ).flatten.each { |container|
          teardown_binary_container.call(container)
        }

        get_containers.call("openbank/lake").each { |container|
          teardown_service_container.call(container)
        }
      end
    rescue Timeout::Error
      #
    end

    FileUtils.cp_r '/metrics/.', '/reports'
    ["/data", "/metrics"].each { |folder|
      FileUtils.rm_rf Dir.glob("#{folder}/*")
    }

    ZMQHelper.stop()

    print "[ suite ended    ]"
  end

end
