require_relative 'eventually_helper'

require 'timeout'
require 'thread'
require 'json'
require 'tempfile'

Thread.abort_on_exception = true

Encoding.default_external = Encoding::UTF_8
Encoding.default_internal = Encoding::UTF_8

class ApplianceHelper

  attr_reader :units

  def get_latest_version(service)
    cmd = ["curl"]
    cmd << ["-ss"]
    cmd << ["-i"]
    cmd << ["-H \"Authorization: token #{ENV['GITHUB_RELEASE_TOKEN']}\""] if ENV.has_key?('GITHUB_RELEASE_TOKEN')
    cmd << ["https://api.github.com/repos/jancajthaml-openbank/#{service}/releases/latest"]
    cmd << ["2>&1 | cat"]

    response = { :code => 0, :raw => [] }
    response[:body] = []

    in_body = false
    IO.popen(cmd.join(" ")) do |stream|
      stream.each do |line|
        response[:raw] << line
        if in_body
          response[:body] << line
        elsif line.start_with? "HTTP/"
          response[:code] = line[9..13].to_i
        elsif line.strip.empty?
          in_body = true
        end
      end
    end

    response[:body] = response[:body].join('')
    response[:raw] = response[:raw].join('\n')

    raise "endpoint is unreachable\n#{response[:raw]}" if response[:code] === 0
    raise "failed to fetch version for #{service}\n#{response[:raw]}" unless response[:code] === 200
    resp_body = JSON.parse(response[:body])
    return resp_body['tag_name'].gsub('v', '')
  end

  def download_artifacts()
    raise "no arch specified" unless ENV.has_key?('UNIT_ARCH')

    arch = ENV['UNIT_ARCH']

    %x(mkdir -p /opt/artifacts)

    cmd = ["FROM alpine"] + [
      "lake",
      "vault",
      "ledger",
      "search"
    ].map { |service|
      version = self.get_latest_version(service)
      "COPY --from=openbank/#{service}:v#{version}-master /opt/artifacts/#{service}_#{version}+master_#{arch}.deb /opt/artifacts/#{service}.deb"
    } + ["RUN ls -la /opt/artifacts"]

    file = Tempfile.new('e2e_artifacts')

    begin
      file.write(cmd.join("\n"))
      file.close

      IO.popen("docker build -t e2e_artifacts - < #{file.path}") do |stream|
        stream.each do |line|
          puts line
        end
      end
      raise "failed to build e2e_artifacts" unless $? == 0

      %x(docker run --name e2e_artifacts-scratch e2e_artifacts /bin/true)
      %x(docker cp e2e_artifacts-scratch:/opt/artifacts/ /opt)
    ensure
      %x(docker rmi -f e2e_artifacts)
      %x(docker rm e2e_artifacts-scratch)
      file.delete
    end
  end

  def install_packages()
    raise "no arch specified" unless ENV.has_key?('UNIT_ARCH')

    [
      "lake",
      "vault",
      "ledger",
      "search",
    ].each { |service|
      # fixme check if file exists

      IO.popen("apt-get -y install -qq -o=Dpkg::Use-Pty=0 -f /opt/artifacts/#{service}.deb 2>&1") do |stream|
        stream.each do |line|
          puts line
        end
      end

      raise "#{service} install failed" unless $? == 0
    }
  end

  def start()
    units = %x(systemctl -t service --no-legend | awk '{ print $1 }' | sort -t @ -k 2 -g)

    @units = units.split("\n").map(&:strip).reject { |x|
      x.empty? || !(
        x.start_with?("vault") ||
        x.start_with?("lake")  ||
        x.start_with?("ledger")  ||
        x.start_with?("search")
      )
    }.map { |x| x.chomp(".service") }

    @units.each { |unit|
      %x(systemctl start #{unit})
    } unless @units.nil?
  end

  def cleanup()
  end

  def ready?()
    actual = %x(systemctl -t service --no-legend | awk '{ print $1 }' | sort -t @ -k 2 -g)
    raise false unless $? == 0

    actual = actual.split("\n").map(&:strip).reject { |x|
      x.empty? || !(
        x.start_with?("vault") ||
        x.start_with?("lake")  ||
        x.start_with?("ledger")  ||
        x.start_with?("search")
      )
    }.map { |x| x.chomp(".service") }

    return @units.all? { |e| actual.include?(e) }
    # fixme check running?
  end

  def update_units()
    units = %x(systemctl -t service --no-legend | awk '{ print $1 }' | sort -t @ -k 2 -g)
    raise false unless $? == 0

    @units = units.split("\n").map(&:strip).reject { |x|
      x.empty? || !(
        x.start_with?("vault") ||
        x.start_with?("lake")  ||
        x.start_with?("ledger")  ||
        x.start_with?("search")
      )
    }.map { |x| x.chomp(".service") }
  end

  def get_metrics(type, filename)
    metrics_file = "/opt/#{type}/metrics/#{filename}"
    return {} unless File.file?(metrics_file)
    return File.open(metrics_file, 'rb') { |f| JSON.parse(f.read) }
  end

  def teardown()
    return if @units.nil?

    @units.each { |unit|
      %x(systemctl stop #{unit})
      %x(journalctl -o short-precise -u #{unit} --no-pager > /reports/logs/#{unit.gsub('@','_')}.log 2>&1)

      if unit.include?("@")
        metrics_file = "/opt/#{unit[/[^@]+/]}/metrics/metrics.#{unit[/([^@]+)$/]}.json"
      else
        metrics_file = "/opt/#{unit}/metrics/metrics.json"
      end

      File.open(metrics_file, 'rb') { |fr|
        File.open("/reports/metrics/#{unit.gsub('@','_')}.json", 'w') { |fw|
          fw.write(fr.read)
        }
      } if File.file?(metrics_file)
    }
  end

end
