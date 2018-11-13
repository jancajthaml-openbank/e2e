require 'turnip/rspec'
require 'thread'

Thread.abort_on_exception = true

RSpec.configure do |config|
  config.raise_error_for_unimplemented_steps = true
  config.color = true

  Dir.glob("./helpers/*_helper.rb") { |f| load f }
  config.include EventuallyHelper, :type => :feature
  #config.include MongoHelper, :type => :feature
  #config.include Journal, :type => :feature
  #config.include Docker, :type => :feature
  Dir.glob("./steps/*_steps.rb") { |f| load f, true }

  $appliance = ApplianceHelper.new()

  config.before(:suite) do |_suite|
    print "[ suite starting ]\n"

    ["/data", "/reports/logs", "/reports/metrics"].each { |folder|
      %x(mkdir -p #{folder})
      %x(rm -rf #{folder}/*)
    }

    $appliance.start()

    print "[ suite started  ]\n"
  end

  config.after(:suite) do |_suite|
    print "\n[ suite ending   ]\n"

    $appliance.teardown()

    print "[ suite ended    ]"
  end

end
