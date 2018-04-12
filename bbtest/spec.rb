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
    print "[ suite starting ]\n"

    ["/data", "/metrics", "/reports"].each { |folder|
      FileUtils.mkdir_p folder
      FileUtils.rm_rf Dir.glob("#{folder}/*")
    }

    $tenant_id = nil
    $http_client = HTTPClient.new()

    print "[ suite started  ]\n"
  end

  config.after(:suite) do |_suite|
    print "\n[ suite ending   ]\n"

    get_containers = lambda do |image|
      containers = %x(docker ps -a | awk '{ print $1,$2 }' | grep #{image} | awk '{print $1 }' 2>/dev/null)
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
      label = %x(docker inspect --format='{{.Name}}' #{container})
      label = ($? == 0 ? label.strip : container)

      %x(docker exec #{container} journalctl -u lake.service -b | cat >/reports/#{label}.log 2>&1)
      %x(docker rm -f #{container} &>/dev/null || :)
    end

    (
      get_containers.call("openbank/wall") <<
      get_containers.call("openbank/search") <<
      get_containers.call("openbank/vault") <<
      get_containers.call("mongo")
    ).flatten.each { |container| teardown_binary_container.call(container) }

    (
      get_containers.call("openbank/lake")
    ).flatten.each { |container| teardown_service_container.call(container) }

    FileUtils.cp_r '/metrics/.', '/reports'
    ["/data", "/metrics"].each { |folder|
      FileUtils.rm_rf Dir.glob("#{folder}/*")
    }

    print "[ suite ended    ]"
  end

end
