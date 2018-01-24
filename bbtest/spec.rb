require 'turnip/rspec'
require 'json'

Thread.abort_on_exception = true

RSpec.configure do |config|
  config.raise_error_for_unimplemented_steps = true
  config.color = true

  Dir.glob("./helpers/*_helper.rb") { |f| load f }
  config.include EventuallyHelper, :type => :feature
  Dir.glob("./steps/*_steps.rb") { |f| load f, true }

  config.before(:suite) do |_suite|
    puts "[info] before suite start"
    FileUtils.rm_rf("/logs/.", secure: true)
    FileUtils.rm_rf("/data/.", secure: true)

    $http_client = HTTPClient.new()
    puts "[info] before suite done"
  end

  config.after(:suite) do |_suite|
    puts ""
    puts "[info] after suite start"
    puts "[info] > teardown vaults"
    vaults = %x(docker ps -aqf "ancestor=openbank/vault" 2>/dev/null)
    vaults.split("\n").each { |container|

      label = %x(docker inspect --format='{{.Name}}' #{container})
      label = $? == 0 ? label.strip : container

      log_path = %x(docker inspect --format='{{.LogPath}}' #{container})
      if $? == 0
        log_path = log_path.strip
        FileUtils.cp(log_path, "/logs/#{label}.jsonlog") if File.file?(log_path)
      end

      %x(docker kill #{container} &>/dev/null || :)
      %x(docker rm -f #{container} &>/dev/null || :)
    } if $? == 0

    puts "[info] > teardown walls"
    walls = %x(docker ps -aqf "ancestor=openbank/wall" 2>/dev/null)
    walls.split("\n").each { |container|

      label = %x(docker inspect --format='{{.Name}}' #{container})
      label = $? == 0 ? label.strip : container

      log_path = %x(docker inspect --format='{{.LogPath}}' #{container})
      if $? == 0
        log_path = log_path.strip
        FileUtils.cp(log_path, "/logs/#{label}.jsonlog") if File.file?(log_path)
      end

      %x(docker kill #{container} &>/dev/null || :)
      %x(docker rm -f #{container} &>/dev/null || :)
    } if $? == 0

    puts "[info] > teardown lakes"
    lakes = %x(docker ps -aqf "ancestor=openbank/lake" 2>/dev/null)
    lakes.split("\n").each { |container|

      label = %x(docker inspect --format='{{.Name}}' #{container})
      label = $? == 0 ? label.strip : container

      log_path = %x(docker inspect --format='{{.LogPath}}' #{container})
      if $? == 0
        log_path = log_path.strip
        FileUtils.cp(log_path, "/logs/#{label}.jsonlog") if File.file?(log_path)
      end

      %x(docker kill #{container} &>/dev/null || :)
      %x(docker rm -f #{container} &>/dev/null || :)
    } if $? == 0
  end
  puts "[info] after suite done"
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
